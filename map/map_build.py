import json
import numpy as np
import triangle as tr
import utm


input_filename = 'Paavo-postinumeroalueet 2019.geojson'
output_filename_code = 'map_code.npz'
output_filename_mesh = 'map_mesh.npz'


def parse_feature_collection(feature_collection):
    if not feature_collection['type'] == 'FeatureCollection':
        raise TypeError()

    # Simply parse each feature in this collection as a list.
    return [parse_feature(it) for it in feature_collection['features']]


def parse_feature(feature):
    if not feature['type'] == 'Feature':
        raise TypeError()

    # Extract the required properties from the feature.
    code = feature['properties']['posti_alue']
    mesh = parse_geometry(feature['geometry'])

    return code, mesh


def parse_geometry(geometry):
    if geometry['type'] == 'MultiPolygon':
        ring_list_list = geometry['coordinates']
    elif geometry['type'] == 'Polygon':
        ring_list_list = [geometry['coordinates']]
    else:
        raise TypeError()

    vertex_list = []
    vertex_index_table = {}

    # Fetch the index corresponding to the vertex if such exists,
    # otherwise assign a new index.
    def vertex_index_fetch(vertex):
        vertex_index = vertex_index_table.get(tuple(vertex), -1)
        if vertex_index == -1:
            vertex_index = len(vertex_list)
            vertex_list.append(vertex)
            vertex_index_table[tuple(vertex)] = vertex_index
        return vertex_index

    edge_list = []
    hole_marker_list = []

    # Add a ring (i.e. a closed loop of vertices) to the vertex list.
    # Additionally, if the ring represents a hole, add a representative point to mark it.
    def add_ring(ring_vertex_list, hole):

        # Construct an indexed list of edges, and append it to the edge list.
        ring_vertex_index_list = [vertex_index_fetch(it) for it in ring_vertex_list]
        ring_edge_list = [list(it) for it in zip(ring_vertex_index_list[:-1], ring_vertex_index_list[1:])]
        edge_list.extend(ring_edge_list)

        # We can compute a representative point (i.e. an arbitrary point inside the ring)
        # by triangulating the ring and computing the center of the first triangle.
        if hole:
            tr_input = {'vertices': vertex_list, 'segments': ring_edge_list}
            tr_output = tr.triangulate(tr_input, opts='p')
            hole_marker = [0.0, 0.0]
            for a in tr_output['triangles'][0]:
                b = tr_output['vertices'][a]
                hole_marker[0] += b[0]
                hole_marker[1] += b[1]
            hole_marker[0] /= 3
            hole_marker[1] /= 3
            hole_marker_list.append(hole_marker)

    # The geometry of an area is represented by multiple lists of rings.
    # In each list, the first ring represents the exterior border
    # and every subsequent ring represents an interior border (i.e. a hole).
    for ring_list in ring_list_list:
        exterior_ring = ring_list[0]
        interior_ring_list = ring_list[1:]
        add_ring(exterior_ring, hole=False)
        for interior_ring in interior_ring_list:
            add_ring(interior_ring, hole=True)

    # Triangulate the combined mesh.
    tr_input = {'vertices': vertex_list, 'segments': edge_list}
    if hole_marker_list:
        tr_input['holes'] = hole_marker_list
    tr_output = tr.triangulate(tr_input, opts='p')
    vertex_list = tr_output['vertices']
    face_list = tr_output['triangles']

    return vertex_list, face_list, edge_list


def project_mesh(mesh):
    # Extract the latitudes and longitudes of each vertex (in WGS84).
    lonlat_array = np.array(mesh[0])
    lat_array = lonlat_array[:, 1]
    lon_array = lonlat_array[:, 0]

    # Use UTM projection with zone 35 to compute the corresponding x and y values.
    x_array, y_array, _, _ = utm.from_latlon(lat_array, lon_array, force_zone_number=35)

    return np.column_stack((x_array, y_array)).tolist(), mesh[1], mesh[2]


def main():

    print('Parsing...')

    with open(input_filename) as file:
        data = parse_feature_collection(json.load(file))

    print('Projecting...')
    
    for i, (code, mesh) in enumerate(data):
        data[i] = code, project_mesh(mesh)

    print('Formatting...')

    vertex_offset = np.insert(np.cumsum([len(it[1][0]) for it in data]), 0, 0)
    face_offset = np.insert(np.cumsum([len(it[1][1]) for it in data]), 0, 0)
    edge_offset = np.insert(np.cumsum([len(it[1][2]) for it in data]), 0, 0)

    code_array = np.empty(len(data), dtype='|S5')
    vertex_array = np.empty(vertex_offset[-1], dtype='2f4, <u2')
    face_array = np.empty(face_offset[-1], dtype='3<u4')
    edge_array = np.empty(edge_offset[-1], dtype='2<u4')

    for i, (code, mesh) in enumerate(data):
        code_array[i] = code

        mesh_vertex_array = np.array(mesh[0])
        mesh_face_array = np.array(mesh[1])
        mesh_edge_array = np.array(mesh[2])

        for j in range(vertex_offset[i + 1] - vertex_offset[i]):
            vertex_array[vertex_offset[i] + j] = mesh_vertex_array[j], i
        face_array[face_offset[i]:face_offset[i + 1]] = mesh_face_array + vertex_offset[i]
        edge_array[edge_offset[i]:edge_offset[i + 1]] = mesh_edge_array + vertex_offset[i]

    print('Saving...')

    np.savez_compressed(output_filename_code, code_array)
    np.savez_compressed(output_filename_mesh, vertex_array, face_array, edge_array)

    # save in different format for WebGL
    webgl_vertex_position_array_le = np.empty(vertex_array.shape[0], dtype='2<f4')
    webgl_vertex_color_index_array_le = np.empty(vertex_array.shape[0], dtype='<u2')
    webgl_face_array_le = face_array
    webgl_edge_array_le = edge_array

    for i in range(vertex_array.shape[0]):
        (x, y), c = vertex_array[i]
        webgl_vertex_position_array_le[i] = (x, y)
        webgl_vertex_color_index_array_le[i] = c

    webgl_vertex_position_array_le.tofile('map_vertex_position.dat')
    webgl_vertex_color_index_array_le.tofile('map_vertex_color_index.dat')
    webgl_face_array_le.tofile('map_face.dat')
    webgl_edge_array_le.tofile('map_edge.dat')

    print(f'* Areas: {len(data)}')
    print(f'* Vertices: {vertex_array.shape[0]}')
    print(f'* Faces: {face_array.shape[0]}')
    print(f'* Edges: {edge_array.shape[0]}')

    print('DONE!')


if __name__ == '__main__':
    main()

import json
import numpy as np
import triangle as tr
import utm
import sys


def build_map_geom(source):

    # Parse the GeoJSON into a dictionary.
    feature_collection = json.loads(source)
    if not feature_collection['type'] == 'FeatureCollection':
        raise TypeError()

    polygon_list_by_code = {}

    # Iterate over the features in the feature collection.
    for feature in feature_collection['features']:
        if not feature['type'] == 'Feature':
            raise TypeError()

        # Extract the postal code and the geometry of the feature.
        code = feature['properties']['posti_alue']
        geom = feature['geometry']

        # Get and existing polygon list or create new one.
        polygon_list = polygon_list_by_code.get(code, [])
        polygon_list_by_code[code] = polygon_list

        # Add the polygons to the list.
        if geom['type'] == 'Polygon':
            polygon_list.append(geom['coordinates'])
        elif geom['type'] == 'MultiPolygon':
            polygon_list.extend(geom['coordinates'])
        else:
            raise TypeError()

    mesh_by_code = {}

    # Build one mesh for each postal code.
    for code, polygon_list in polygon_list_by_code.items():
        mesh_list = [create_polygon_mesh(polygon) for polygon in polygon_list]
        mesh_by_code[code] = combine_mesh_list(mesh_list, has_index=False)

    # Sort the meshes by postal code.
    mesh_list = list(map(lambda it: it[1], sorted(mesh_by_code.items(), key=lambda it: it[0])))

    # Add postal code information to each separate mesh and then combine them into one mesh.
    for i, mesh in enumerate(mesh_list):
        augment_mesh_index(mesh, i)
    mesh = combine_mesh_list(mesh_list, has_index=True)

    vertex_count = mesh['vertex_position'].shape[0]
    vertex_array = np.empty(vertex_count, dtype='2<f4, <u2')
    for i in range(vertex_count):
        position = mesh['vertex_position'][i]
        region_pointer = mesh['vertex_region_pointer'][i]
        vertex_array[i] = position, region_pointer

    element_array = mesh['element_vertex_pointer'].astype('<u4')

    build_context_data(mesh)

    element_middle_array = mesh['element_middle'].astype('<f8')
    element_extent_array = mesh['element_extent'].astype('<f8')

    return {
        'vertex_data': vertex_array,
        'element_data': element_array,
        'element_middle': element_middle_array,
        'element_extent': element_extent_array
    }


def build_and_save_map_geom(source):
    map_geom = build_map_geom(source)
    np.savez_compressed('map_geom.npz', **map_geom)


def load_map_geom():
    map_geom = np.load('map_geom.npz')
    if sys.byteorder == 'big':
        for it in map_geom.values():
            it.byteswap()
    return map_geom


def make_indirect(vertex_list_list):

    vertex_list = []
    vertex_pointer_table = {}

    # Fetch the vertex pointer corresponding to the given vertex.
    # If necessary, assign a new pointer.
    def vertex_pointer(vertex):
        pointer = vertex_pointer_table.get(tuple(vertex), -1)
        if pointer == -1:
            pointer = len(vertex_list)
            vertex_list.append(vertex)
            vertex_pointer_table[tuple(vertex)] = pointer
        return pointer

    # Create an indirect version of the polygon, i.e. version with indexed vertices.
    vertex_pointer_list_list = []
    for ring_vertex_list in vertex_list_list:
        ring_vertex_pointer_list = [vertex_pointer(it) for it in ring_vertex_list]
        vertex_pointer_list_list.append(ring_vertex_pointer_list)

    return vertex_list, vertex_pointer_list_list


def project(vertex_list):

    # Extract the latitudes and longitudes of each vertex (in WGS84).
    lonlat_array = np.array(vertex_list)
    lat_array = lonlat_array[:, 1]
    lon_array = lonlat_array[:, 0]

    # Use UTM projection with zone 35 to compute the corresponding x and y values.
    x_array, y_array, _, _ = utm.from_latlon(lat_array, lon_array, force_zone_number=35)

    # Return the projected vertices.
    return np.column_stack((x_array, y_array)).tolist()


def create_polygon_mesh(vertex_ring_list):

    vertex_list, vertex_pointer_ring_list = make_indirect(vertex_ring_list)
    vertex_list = project(vertex_list)

    vertex_position_offset_list = []

    segment_list = []
    hole_list = []

    for i, vertex_pointer_ring in enumerate(vertex_pointer_ring_list):

        # Each segment is represented by a pair of vertex pointers.
        # We can zip the vertex pointer list with an offset of one to get such representation.
        ring_segment_list = [list(it) for it in zip(vertex_pointer_ring[:-1], vertex_pointer_ring[1:])]

        segment_list.extend(ring_segment_list)

        # The first ring is the exterior ring, while the subsequent rings are interior.
        # Each interior ring represents a hole, that we mark by a representative point.
        # We have to compute an arbitrary point within the hole, which we can get by choosing
        # the middle of some triangle in the triangulation of the hole.
        if i > 0:

            # Triangulate the hole.
            ring_tr_input = {'vertices': vertex_list, 'segments': ring_segment_list}
            ring_tr_output = tr.triangulate(ring_tr_input, opts='p')

            # Compute the middle of the first triangle in the triangulation.
            ring_hole = [0.0, 0.0]
            for a in ring_tr_output['triangles'][0]:
                b = ring_tr_output['vertices'][a]
                ring_hole[0] += b[0]
                ring_hole[1] += b[1]
            ring_hole[0] /= 3
            ring_hole[1] /= 3

            hole_list.append(ring_hole)

        # Drop the last vertex to get a list of unique vertices.
        vertex_pointer_list = vertex_pointer_ring[:-1]

        for j in range(len(vertex_pointer_list)):

            # Find the positions of the previous, current and next vertex.
            p0 = np.array(vertex_list[vertex_pointer_list[j - 1]])
            p1 = np.array(vertex_list[vertex_pointer_list[j]])
            p2 = np.array(vertex_list[vertex_pointer_list[(j + 1) % len(vertex_pointer_list)]])

            # Compute the incoming and outgoing edge vectors for the current vertex.
            v01 = p1 - p0
            v01 /= np.linalg.norm(v01)
            v12 = p2 - p1
            v12 /= np.linalg.norm(v12)

            # Compute the normal for the incoming edge vector.
            normal = np.array((-v01[1], v01[0]))

            # Compute the tangent for the current vertex.
            tangent = v01 + v12
            tangent /= np.linalg.norm(tangent)

            # Compute and scale the tangent normal.
            # This is one of the two vertex offset vectors, we get the other one by taking the inverse.
            offset = np.array((-tangent[1], tangent[0]))
            offset /= offset.dot(normal)

            # Cheap miter limit.
            if np.linalg.norm(offset) > 20:
                offset = offset * (20 / np.linalg.norm(offset))

            vertex_position_offset_list.append(offset)

    # Triangulate the complete polygon.
    tr_input = {'vertices': vertex_list, 'segments': segment_list}
    if hole_list:
        tr_input['holes'] = hole_list
    tr_output = tr.triangulate(tr_input, opts='p')

    vertex_position_list = tr_output['vertices']
    element_list = tr_output['triangles']

    mesh = {
        'vertex_position': np.array(vertex_position_list, dtype=np.float),
        'vertex_position_offset': np.array(vertex_position_offset_list, dtype=np.float),
        'element_vertex_pointer': np.array(element_list, dtype=np.int)
    }

    return mesh


def augment_mesh_index(mesh, vertex_index):
    mesh['vertex_region_pointer'] = np.full(mesh['vertex_position'].shape[0], vertex_index, dtype=np.int)


def combine_mesh_list(mesh_list, has_index):

    # Compute offset for each sub-mesh.
    vertex_offset = np.insert(np.cumsum([mesh['vertex_position'].shape[0] for mesh in mesh_list]), 0, 0)
    element_offset = np.insert(np.cumsum([mesh['element_vertex_pointer'].shape[0] for mesh in mesh_list]), 0, 0)

    # Create the new arrays.
    vertex_position_array = np.empty((vertex_offset[-1], 2), dtype=np.float)
    vertex_position_offset_array = np.empty((vertex_offset[-1], 2), dtype=np.float)
    vertex_region_pointer_array = np.empty(vertex_offset[-1], dtype=np.int) if has_index else None
    element_vertex_pointer_array = np.empty((element_offset[-1], 3), dtype=np.int)

    # Iterate over the sub-meshes and copy the arrays.
    # Shift values if necessary.
    for i, mesh in enumerate(mesh_list):

        vertex_position_array[vertex_offset[i]:vertex_offset[i + 1]] = mesh['vertex_position']
        vertex_position_offset_array[vertex_offset[i]:vertex_offset[i + 1]] = mesh['vertex_position_offset']

        if has_index:
            vertex_region_pointer_array[vertex_offset[i]:vertex_offset[i + 1]] = mesh['vertex_region_pointer']

        element_vertex_pointer_array[element_offset[i]:element_offset[i + 1]] =\
            mesh['element_vertex_pointer'] + vertex_offset[i]

    mesh = {
        'vertex_position': vertex_position_array,
        'vertex_position_offset': vertex_position_offset_array,
        'element_vertex_pointer': element_vertex_pointer_array
    }
    if has_index:
        mesh['vertex_region_pointer'] = vertex_region_pointer_array

    return mesh


def build_context_data(mesh):
    vertex_array = mesh['vertex_position']
    element_array = mesh['element_vertex_pointer']
    element_middle_array = np.empty((element_array.shape[0], 2), dtype=np.float)
    element_extent_array = np.empty(element_array.shape[0], dtype=np.float)
    for i in range(element_array.shape[0]):
        a = vertex_array[element_array[i][0]]
        b = vertex_array[element_array[i][1]]
        c = vertex_array[element_array[i][2]]
        middle = (np.max((a, b, c), axis=0) + np.min((a, b, c), axis=0)) / 2
        extent = np.max(np.linalg.norm(np.array([a, b, c]) - middle, ord=np.inf))
        element_middle_array[i] = middle
        element_extent_array[i] = extent
    mesh['element_middle'] = element_middle_array
    mesh['element_extent'] = element_extent_array


if __name__ == '__main__':
    source_filename = 'Paavo-postinumeroalueet 2019.geojson'
    with open(source_filename, encoding='utf-8') as source_file:
        build_and_save_map_geom(source_file.read())

from pyglet import app
from pyglet.gl import *
from pyglet.window import key, mouse, Window
import numpy as np
from scipy.spatial import cKDTree
from ctypes import *
import math

from map_meta_tools import load_map_meta
from map_geom_tools import load_map_geom
from map_plot_tools import load_map_plot

view_width = 640
view_height = 480

config = Config(sample_buffers=1, samples=8, double_buffer=True)
window = Window(config=config, width=view_width, height=view_height, resizable=True, caption='<none>')

VERTEX_SHADER_SOURCE = b'''
#version 330
layout(location = 0) in vec2 a_position;
layout(location = 1) in int a_region;

out vec4 v_color;

uniform mat3 u_map_to_clip;

layout(std140) uniform u_region_color_block {
    vec4 u_region_color[3026];
};

void main()
{
    v_color = u_region_color[a_region];
    vec2 v_position = (u_map_to_clip * vec3(a_position, 1.0)).xy;
    gl_Position = vec4(v_position, 0.0, 1.0);
}
'''

FRAGMENT_SHADER_SOURCE = b'''
#version 330
in vec4 v_color;

out vec4 f_color;

void main()
{
    f_color = v_color;
}
'''

map_meta = load_map_meta()
map_geom = load_map_geom()
map_plot = load_map_plot()

vertex_array = map_geom['vertex_data']
element_array = map_geom['element_data']

color_array_dict = {
    key.A: map_plot['age_data'],
    key.W: map_plot['water_data'],
    key.F: map_plot['forest_data'],
    key.C: map_plot['cluster_data']
}


def build_shader(shader_info):
    shader = glCreateShader(shader_info['type'])
    glShaderSource(shader, 1,
                   pointer(cast(c_char_p(shader_info['source']), POINTER(GLchar))),
                   pointer(GLint(len(shader_info['source']))))
    glCompileShader(shader)
    return shader


def build_shader_program(shader_info_list):
    shader_list = []
    for shader_info in shader_info_list:
        shader_list.append(build_shader(shader_info))
    shader_program = glCreateProgram()
    for shader in shader_list:
        glAttachShader(shader_program, shader)
    glLinkProgram(shader_program)
    for shader in shader_list:
        glDetachShader(shader_program, shader)
    return shader_program


shader_program = build_shader_program([
    {'type': GL_VERTEX_SHADER, 'source': VERTEX_SHADER_SOURCE},
    {'type': GL_FRAGMENT_SHADER, 'source': FRAGMENT_SHADER_SOURCE}
])


uniform_map_to_clip = glGetUniformLocation(shader_program, c_char_p(b'u_map_to_clip'))


def update_buffer_content(buffer_type, buffer, buffer_data, buffer_usage):
    glBindBuffer(buffer_type, buffer)
    glBufferData(buffer_type, buffer_data.nbytes, buffer_data.ctypes.data_as(POINTER(GLvoid)), buffer_usage)
    glBindBuffer(buffer_type, 0)


def build_buffer(buffer_type, buffer_data, buffer_usage):
    buffer = GLuint()
    glGenBuffers(1, pointer(buffer))
    update_buffer_content(buffer_type, buffer, buffer_data, buffer_usage)
    buffer_element_size = buffer_data.nbytes // buffer_data.shape[0]
    buffer_element_count = buffer_data.nbytes // buffer_element_size
    return buffer, buffer_element_size, buffer_element_count


vertex_buffer, vertex_size, _ = build_buffer(GL_ARRAY_BUFFER, vertex_array, GL_STATIC_DRAW)
element_buffer, element_size, element_count = build_buffer(GL_ELEMENT_ARRAY_BUFFER, element_array, GL_STATIC_DRAW)
region_color_buffer, _, _ = build_buffer(GL_UNIFORM_BUFFER, color_array_dict[key.F], GL_DYNAMIC_DRAW)


def on_launch():
    uniform_region_color_block = glGetUniformBlockIndex(shader_program, c_char_p(b'u_region_color_block'))
    glUniformBlockBinding(shader_program, uniform_region_color_block, 0)
    glBindBufferBase(GL_UNIFORM_BUFFER, 0, region_color_buffer)

    glBindBuffer(GL_ARRAY_BUFFER, vertex_buffer)

    glEnableVertexAttribArray(0)
    glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, vertex_size, 0)

    glEnableVertexAttribArray(1)
    glVertexAttribIPointer(1, 1, GL_UNSIGNED_SHORT, vertex_size, 2 * sizeof(GLfloat))

    glBindBuffer(GL_ARRAY_BUFFER, 0)


log_zoom = -8.0

mat_view_to_clip = None
mat_map_to_view = None

map_origin_x = (83748.4296875 + 732907.75) / 2
map_origin_y = (6629044.0 + 7776450.0) / 2
map_offset_x = 0.0
map_offset_y = 0.0


def update_view():
    global mat_view_to_clip, mat_map_to_view

    zoom = math.exp(log_zoom)
    mid_x = map_origin_x + map_offset_x
    mid_y = map_origin_y + map_offset_y

    mat_view_to_clip = np.array([[2 / window.width, 0, -1],
                                 [0, 2 / window.height, -1],
                                 [0, 0, 1]], dtype='=f4')

    mat_map_to_view = np.array([[zoom, 0, window.width / 2 - zoom * mid_x],
                                [0, zoom, window.height / 2 - zoom * mid_y],
                                [0, 0, 1]], dtype='=f4')


centroid_tree = cKDTree(map_geom['element_middle'])
centroid_tree_radius = np.max(map_geom['element_extent'])


def find_region_by_map_position(map_position):

    def is_point_in_triangle(p, p0, p1, p2):
        d1 = p - p2
        d2 = p1 - p2
        d = d2[1] * (p0[0] - p2[0]) - d2[0] * (p0[1] - p2[1])
        s = d2[1] * d1[0] - d2[0] * d1[1]
        t = (p2[1] - p0[1]) * d1[0] + (p0[0] - p2[0]) * d1[1]
        if d < 0:
            return s <= 0 and t <= 0 and s + t >= d
        return s >= 0 and t >= 0 and s + t <= d

    i_candidates = centroid_tree.query_ball_point(vec_mouse_map_position[:2], centroid_tree_radius, p=np.inf)

    for i in i_candidates:
        a = vertex_array[element_array[i][0]]
        b = vertex_array[element_array[i][1]]
        c = vertex_array[element_array[i][2]]

        if is_point_in_triangle(map_position[:2], a[0], b[0], c[0]):
            return a[1]

    return None


vec_mouse_view_position = None
vec_mouse_map_position = None
fix_mouse_map_position = False


@window.event
def on_key_press(symbol, modifiers):
    if symbol in color_array_dict.keys():
        update_buffer_content(GL_UNIFORM_BUFFER, region_color_buffer, color_array_dict[symbol], GL_DYNAMIC_DRAW)


@window.event
def on_key_release(symbol, modifiers):
    pass


@window.event
def on_mouse_press(x, y, button, modifiers):
    global fix_mouse_map_position
    if button == mouse.LEFT:
        window.set_mouse_cursor(window.get_system_mouse_cursor(Window.CURSOR_SIZE))
        fix_mouse_map_position = True
    if button == mouse.RIGHT:
        region = find_region_by_map_position(vec_mouse_map_position[:2])
        if region is not None:
            code = map_meta['region_code_data'][region]
            name = map_meta['region_name_data'][region]
            window.set_caption(f'{code} {name}')
        else:
            window.set_caption('<none>')


@window.event
def on_mouse_release(x, y, button, modifiers):
    global fix_mouse_map_position
    if button == mouse.LEFT:
        window.set_mouse_cursor(None)
        fix_mouse_map_position = False


@window.event
def on_mouse_motion(x, y, dx, dy):
    global vec_mouse_view_position, vec_mouse_map_position
    global mat_map_to_view
    vec_mouse_view_position = np.array((x, y, 1.0))
    vec_mouse_map_position = np.linalg.inv(mat_map_to_view) @ np.array((x, y, 1.0))


@window.event
def on_mouse_enter(x, y):
    pass


@window.event
def on_mouse_leave(x, y):
    global vec_mouse_view_position
    vec_mouse_view_position = None


@window.event
def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
    global vec_mouse_map_position
    global mat_map_to_view
    global map_offset_x, map_offset_y
    new_vec_mouse_map_position = np.linalg.inv(mat_map_to_view) @ np.array((x, y, 1.0))
    if not fix_mouse_map_position:
        vec_mouse_map_position = new_vec_mouse_map_position
    else:
        map_offset_x += vec_mouse_map_position[0] - new_vec_mouse_map_position[0]
        map_offset_y += vec_mouse_map_position[1] - new_vec_mouse_map_position[1]
        update_view()


@window.event
def on_mouse_scroll(x, y, scroll_x, scroll_y):
    global log_zoom
    log_zoom = np.clip(log_zoom + 0.1 * scroll_y, -8.0, -2.0)

    global mat_map_to_view
    global vec_mouse_map_position
    global map_offset_x, map_offset_y

    update_view()
    new_vec_mouse_map_position = np.linalg.inv(mat_map_to_view) @ np.array((x, y, 1.0))
    map_offset_x += vec_mouse_map_position[0] - new_vec_mouse_map_position[0]
    map_offset_y += vec_mouse_map_position[1] - new_vec_mouse_map_position[1]
    update_view()


@window.event
def on_resize(width, height):
    global view_width, view_height

    # avoid width == 0, height == 0
    view_width = max(width, 1)
    view_height = max(height, 1)

    update_view()


@window.event
def on_draw():
    glViewport(0, 0, view_width, view_height)

    # clear screen
    glClearColor(1.0, 1.0, 1.0, 1.0)
    glClear(GL_COLOR_BUFFER_BIT)

    glUseProgram(shader_program)

    # update projection matrix
    global mat_view_to_clip, mat_map_to_view
    map_to_clip = mat_view_to_clip @ mat_map_to_view
    glUniformMatrix3fv(uniform_map_to_clip, 1, GL_TRUE, map_to_clip.ctypes.data_as(POINTER(GLfloat)))

    # bind vertices
    glBindBuffer(GL_ARRAY_BUFFER, vertex_buffer)

    # bind and draw elements
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, element_buffer)
    glDrawElements(GL_TRIANGLES, element_count * 3, GL_UNSIGNED_INT, 0)

    # remove bindings
    glBindBuffer(GL_ARRAY_BUFFER, 0)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)

    glUseProgram(0)

    glFlush()


on_launch()
app.run()

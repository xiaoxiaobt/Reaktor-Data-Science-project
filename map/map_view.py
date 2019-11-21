from pyglet.gl import *
from pyglet.window import mouse
import numpy as np
from ctypes import *
import math
import random

from map_meta_tools import load_map_meta
from map_geom_tools import load_map_geom

config = pyglet.gl.Config(sample_buffers=1, samples=8, double_buffer=True)
window = pyglet.window.Window(config=config, resizable=True)

VERTEX_SHADER_SOURCE = b'''
#version 330
layout(location = 0) in vec2 position;
layout(location = 1) in int color_index;

out vec4 color;

uniform mat3 world_to_view;

layout(std140) uniform color_table_block {
    vec4 color_table[3026];
};

void main()
{
    color = color_table[color_index];
    vec3 new_position = world_to_view * vec3(position, 1.0);
    gl_Position = vec4(new_position.xy, 0.0, 1.0);
}
'''

FRAGMENT_SHADER_SOURCE = b'''
#version 330 compatibility
in vec4 color;

void main()
{
    gl_FragColor = color;
}
'''

map_meta = load_map_meta()
map_geom = load_map_geom()

vertex_array = map_geom['vertex_data']
element_array = map_geom['element_data']

color_table_array = np.empty(3026, dtype='4=f4')
for i in range(color_table_array.shape[0]):
    r = random.random()
    g = random.random()
    b = random.random()
    color_table_array[i] = r, g, b, 1.0


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


world_to_view_uniform = glGetUniformLocation(shader_program, c_char_p(b'world_to_view'))


def build_buffer(buffer_type, buffer_data, buffer_usage):
    buffer = GLuint()
    glGenBuffers(1, pointer(buffer))
    glBindBuffer(buffer_type, buffer)
    glBufferData(buffer_type, buffer_data.nbytes, buffer_data.ctypes.data_as(POINTER(GLvoid)), buffer_usage)
    glBindBuffer(buffer_type, 0)
    buffer_element_size = buffer_data.nbytes // buffer_data.shape[0]
    buffer_element_count = buffer_data.nbytes // buffer_element_size
    return buffer, buffer_element_size, buffer_element_count


vertex_buffer, vertex_size, _ = build_buffer(GL_ARRAY_BUFFER, vertex_array, GL_STATIC_DRAW)
element_buffer, element_size, element_count = build_buffer(GL_ELEMENT_ARRAY_BUFFER, element_array, GL_STATIC_DRAW)
color_table_buffer, _, _ = build_buffer(GL_UNIFORM_BUFFER, color_table_array, GL_DYNAMIC_DRAW)

color_table_uniform_block = glGetUniformBlockIndex(shader_program, c_char_p(b'color_table_block'))
glUniformBlockBinding(shader_program, color_table_uniform_block, 0)
glBindBufferBase(GL_UNIFORM_BUFFER, 0, color_table_buffer)

glBindBuffer(GL_ARRAY_BUFFER, vertex_buffer)

glEnableVertexAttribArray(0)
glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, vertex_size, 0)

glEnableVertexAttribArray(1)
glVertexAttribIPointer(1, 1, GL_UNSIGNED_SHORT, vertex_size, 2 * sizeof(GLfloat))

glBindBuffer(GL_ARRAY_BUFFER, 0)

x_mid = (83748.4296875 + 732907.75) / 2
y_mid = (6629044.0 + 7776450.0) / 2
x_mid_off = 0
y_mid_off = 0
log_zoom = -8.0


def build_view():
    zoom = math.exp(log_zoom)
    xmid = x_mid + x_mid_off
    ymid = y_mid + y_mid_off

    view_to_clip = np.array([[2 / window.width, 0, -1],
                             [0, 2 / window.height, -1],
                             [0, 0, 1]], dtype='=f4')
    map_to_view = np.array([[zoom, 0, window.width / 2 - zoom * xmid],
                            [0, zoom, window.height / 2 - zoom * ymid],
                            [0, 0, 1]], dtype='=f4')

    return map_to_view, view_to_clip


mouse_pre = None
mouse_now = None


@window.event
def on_mouse_press(x, y, button, modifiers):
    global mouse_pre
    if button == mouse.LEFT:
        mouse_pre = (x, y)


@window.event
def on_mouse_release(x, y, button, modifiers):
    global mouse_pre, mouse_now
    mouse_now = (x, y)
    if button == mouse.LEFT:
        global x_mid, y_mid
        global x_mid_off, y_mid_off
        dx = -(mouse_now[0] - mouse_pre[0])
        dy = -(mouse_now[1] - mouse_pre[1])
        zoom = math.exp(log_zoom)
        x_mid_off = dx / zoom
        y_mid_off = dy / zoom
        x_mid += x_mid_off
        y_mid += y_mid_off
        x_mid_off = 0
        y_mid_off = 0
        mouse_pre = None
        mouse_now = None


@window.event
def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
    global mouse_now
    mouse_now = (x, y)
    if buttons & mouse.LEFT:
        global x_mid_off, y_mid_off
        dx = -(mouse_now[0] - mouse_pre[0])
        dy = -(mouse_now[1] - mouse_pre[1])
        zoom = math.exp(log_zoom)
        x_mid_off = dx / zoom
        y_mid_off = dy / zoom


@window.event
def on_mouse_scroll(x, y, scroll_x, scroll_y):
    global x_mid, y_mid

    xmid = x_mid + x_mid_off
    ymid = y_mid + y_mid_off

    global log_zoom
    zoom = math.exp(log_zoom)
    world_to_window = np.array([[zoom, 0, window.width / 2 - zoom * xmid],
                                [0, zoom, window.height / 2 - zoom * ymid],
                                [0, 0, 1]], dtype='=f4')

    window_to_world = np.linalg.inv(world_to_window)
    world_x, world_y, _ = window_to_world @ (x, y, 1)

    log_zoom += 0.1 * scroll_y
    if log_zoom < -8.0:
        log_zoom = -8.0
    elif log_zoom > -2.0:
        log_zoom = -2.0

    zoom = math.exp(log_zoom)
    world_to_window = np.array([[zoom, 0, window.width / 2 - zoom * xmid],
                                [0, zoom, window.height / 2 - zoom * ymid],
                                [0, 0, 1]], dtype='=f4')

    window_to_world = np.linalg.inv(world_to_window)
    world_x_new, world_y_new, _ = window_to_world @ (x, y, 1)

    x_mid += world_x - world_x_new
    y_mid += world_y - world_y_new


@window.event
def on_resize(width, height):

    # avoid width == 0, height == 0
    width = max(width, 1)
    height = max(height, 1)

    glViewport(0, 0, width, height)


@window.event
def on_draw():

    # clear screen
    glClearColor(1.0, 1.0, 1.0, 1.0)
    glClear(GL_COLOR_BUFFER_BIT)

    glUseProgram(shader_program)

    # update projection matrix
    map_to_view, view_to_clip = build_view()
    map_to_clip = view_to_clip @ map_to_view
    glUniformMatrix3fv(world_to_view_uniform, 1, GL_TRUE, map_to_clip.ctypes.data_as(POINTER(GLfloat)))

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


pyglet.app.run()

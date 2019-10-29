#!/usr/bin/env python

from pyglet.gl import *
from pyglet.window import mouse
import numpy as np
from ctypes import *
import sys
import math
from random import random

config = pyglet.gl.Config(sample_buffers=1, samples=8, double_buffer=True)
window = pyglet.window.Window(config=config, resizable=True)

VERTEX_SHADER_SOURCE = b'''
#version 330
layout(location = 0) in vec2 position;
layout(location = 1) in int color_index;

out vec4 color;

uniform mat3 world_to_view;

uniform bool color_fetch;
layout(std140) uniform color_table_block {
    vec4 color_table[3026];
};

void main()
{
    if (color_fetch)
        color = color_table[color_index];
    else
        color = vec4(0.0, 0.0, 0.0, 1.0);
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

data = np.load('map.npz')

vertex_array = data['v']
face_array = data['f']
edge_array = data['e']

if sys.byteorder == 'big':
    vertex_array.byteswap()
    face_array.byteswap()
    edge_array.byteswap()

color_table_array = np.empty(3026, dtype='4=f4')
for i in range(color_table_array.shape[0]):
    color_table_array[i] = random() * 0.4 + 0.3, 0.4, random() * 0.6 + 0.4, 1.0

vertex_buffer = GLuint()
vertex_buffer_data = vertex_array.ctypes.data_as(POINTER(GLvoid))
vertex_size = 2 * sizeof(GLfloat) + sizeof(GLushort)
vertex_buffer_size = vertex_array.shape[0] * vertex_size

face_buffer = GLuint()
face_buffer_data = face_array.ctypes.data_as(POINTER(GLuint))
face_size = 3 * sizeof(GLuint)
face_buffer_size = face_array.shape[0] * face_size

edge_buffer = GLuint()
edge_buffer_data = edge_array.ctypes.data_as(POINTER(GLuint))
edge_size = 2 * sizeof(GLuint)
edge_buffer_size = edge_array.shape[0] * edge_size

color_table_buffer = GLuint()
color_table_buffer_data = color_table_array.ctypes.data_as(POINTER(GLvoid))
color_table_buffer_size = 4 * sizeof(GLfloat) * color_table_array.shape[0]

vertex_shader = glCreateShader(GL_VERTEX_SHADER)
glShaderSource(vertex_shader, 1,
               pointer(cast(c_char_p(VERTEX_SHADER_SOURCE), POINTER(GLchar))),
               pointer(GLint(len(VERTEX_SHADER_SOURCE))))
glCompileShader(vertex_shader)

fragment_shader = glCreateShader(GL_FRAGMENT_SHADER)
glShaderSource(fragment_shader, 1,
               pointer(cast(c_char_p(FRAGMENT_SHADER_SOURCE), POINTER(GLchar))),
               pointer(GLint(len(FRAGMENT_SHADER_SOURCE))))
glCompileShader(fragment_shader)

shader_program = glCreateProgram()
glAttachShader(shader_program, vertex_shader)
glAttachShader(shader_program, fragment_shader)
glLinkProgram(shader_program)

glDetachShader(shader_program, vertex_shader)
glDetachShader(shader_program, fragment_shader)

world_to_view_uniform = glGetUniformLocation(shader_program, c_char_p(b'world_to_view'))
color_fetch_uniform = glGetUniformLocation(shader_program, c_char_p(b'color_fetch'))

glGenBuffers(1, pointer(color_table_buffer))
glBindBuffer(GL_UNIFORM_BUFFER, color_table_buffer)
glBufferData(GL_UNIFORM_BUFFER, color_table_buffer_size, color_table_buffer_data, GL_DYNAMIC_DRAW)
glBindBuffer(GL_UNIFORM_BUFFER, 0)

color_table_uniform_block = glGetUniformBlockIndex(shader_program, c_char_p(b'color_table_block'))
glUniformBlockBinding(shader_program, color_table_uniform_block, 0)
glBindBufferBase(GL_UNIFORM_BUFFER, 0, color_table_buffer)

glGenBuffers(1, pointer(vertex_buffer))
glBindBuffer(GL_ARRAY_BUFFER, vertex_buffer)
glBufferData(GL_ARRAY_BUFFER, vertex_buffer_size, vertex_buffer_data, GL_STATIC_DRAW)

glGenBuffers(1, pointer(face_buffer))
glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, face_buffer)
glBufferData(GL_ELEMENT_ARRAY_BUFFER, face_buffer_size, face_buffer_data, GL_STATIC_DRAW)

glGenBuffers(1, pointer(edge_buffer))
glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, edge_buffer)
glBufferData(GL_ELEMENT_ARRAY_BUFFER, edge_buffer_size, edge_buffer_data, GL_STATIC_DRAW)

glEnableVertexAttribArray(0)
glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, vertex_size, 0)

glEnableVertexAttribArray(1)
glVertexAttribIPointer(1, 1, GL_UNSIGNED_SHORT, vertex_size, 2 * sizeof(GLfloat))

glBindBuffer(GL_ARRAY_BUFFER, 0)
glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)

x_mid = (83748.4296875 + 732907.75) / 2
y_mid = (6629044.0 + 7776450.0) / 2
x_mid_off = 0
y_mid_off = 0
log_zoom = -8.0

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
    glClearColor(0.8, 0.9, 1.0, 1.0)
    glClear(GL_COLOR_BUFFER_BIT)

    glUseProgram(shader_program)

    xmid = x_mid + x_mid_off
    ymid = y_mid + y_mid_off

    zoom = math.exp(log_zoom)

    # update projection matrix
    window_to_view = np.array([[2 / window.width, 0, -1],
                               [0, 2 / window.height, -1],
                               [0, 0, 1]], dtype='=f4')
    world_to_window = np.array([[zoom, 0, window.width / 2 - zoom * xmid],
                                [0, zoom, window.height / 2 - zoom * ymid],
                                [0, 0, 1]], dtype='=f4')
    world_to_view = window_to_view @ world_to_window
    glUniformMatrix3fv(world_to_view_uniform, 1, GL_TRUE, world_to_view.ctypes.data_as(POINTER(GLfloat)))

    # bind vertices
    glBindBuffer(GL_ARRAY_BUFFER, vertex_buffer)

    # bind and draw faces
    glUniform1i(color_fetch_uniform, 1)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, face_buffer)
    glDrawElements(GL_TRIANGLES, face_buffer_size // sizeof(GLuint), GL_UNSIGNED_INT, 0)

    # bind and draw edges
    glUniform1i(color_fetch_uniform, 0)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, edge_buffer)
    glDrawElements(GL_LINES, edge_buffer_size // sizeof(GLuint), GL_UNSIGNED_INT, 0)

    # remove bindings
    glBindBuffer(GL_ARRAY_BUFFER, 0)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)

    glUseProgram(0)

    glFlush()


pyglet.app.run()

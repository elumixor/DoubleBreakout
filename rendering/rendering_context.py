from __future__ import annotations

import sys
from typing import Tuple

import glfw
import numpy as np
from OpenGL.GL import *

from .color import Color
from .game_objects import GameObject


class RenderingContext:
    __static_instance = None

    def __init__(self, width, height, title=""):
        self.height = height
        self.width = width

        if not glfw.init():
            print("glfw.init() failed", file=sys.stderr)
            return

        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 1)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, GL_TRUE)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        self.window = glfw.create_window(width, height, title, None, None)

        if not self.window:
            print("Could not create window", file=sys.stderr)
            glfw.terminate()
            return

        glfw.make_context_current(self.window)

        self._clear_color = Color.black
        glClearColor(0.0, 0.0, 0.0, 1.0)

        # Enable blending
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Enable backface culling
        glEnable(GL_CULL_FACE)

        VAO = glGenVertexArrays(1)
        glBindVertexArray(VAO)

        self._main_scene = GameObject()

        # Constant AR
        self.aspect = width / height
        self._projection_matrix = np.array([[1, 0, 0], [0, self.aspect, 0], [0, 0, 1]], dtype=np.float32)

        def resize_callback(window, width, height):
            self.resize(width, height)

        glfw.set_framebuffer_size_callback(self.window, resize_callback)

        self.keys_down = []

        def on_key_event(window, key, scancode, action, mods):
            if action == glfw.PRESS:
                self.keys_down.append(key)

        glfw.set_key_callback(self.window, on_key_event)

        # Set up rendering to the texture
        self.fb = glGenFramebuffers(1)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.terminate()

    def __del__(self):
        self.terminate()

    def terminate(self):
        try:
            glfw.terminate()
        except TypeError:
            pass

        RenderingContext.__static_instance = None

    def resize(self, width: float, height: float):
        self.width = width
        self.height = height
        self.aspect = width / height
        glViewport(0, 0, width, height)
        self._projection_matrix = np.array([[1, 0, 0], [0, self.aspect, 0], [0, 0, 1]], dtype=np.float32)

    @classmethod
    def instance(cls) -> RenderingContext:
        try:
            if cls.__static_instance is None:
                instance = RenderingContext(800, 600)
                cls.__static_instance = instance

            return cls.__static_instance
        except AttributeError:
            instance = RenderingContext(800, 600)
            # noinspection PyAttributeOutsideInit
            cls.__static_instance = instance
            return instance

    @property
    def clear_color(self):
        return self._clear_color

    @clear_color.setter
    def clear_color(self, value: Color):
        self._clear_color = value
        glClearColor(*value.to_numpy)

    @property
    def main_scene(self):
        return self._main_scene

    @property
    def camera_position(self) -> Tuple[float, float]:
        dx = self._projection_matrix[0][-1]
        dy = self._projection_matrix[1][-1]
        return -dx, -dy / self.aspect

    @camera_position.setter
    def camera_position(self, position: Tuple[float, float]):
        dx, dy = position
        self._projection_matrix[0][-1] = -dx
        self._projection_matrix[1][-1] = -dy * self.aspect

    def render_frame(self):
        self.keys_down = []
        glfw.poll_events()
        glClear(GL_COLOR_BUFFER_BIT)
        self._main_scene.render(self._projection_matrix)
        glfw.swap_buffers(self.window)

    def render(self):
        while not glfw.window_should_close(self.window) and not self.is_key_pressed(glfw.KEY_ESCAPE):
            self.render_frame()

        glfw.terminate()

    def is_key_pressed(self, key):
        return key in self.keys_down

    def is_key_held(self, key):
        return glfw.get_key(self.window, key) == glfw.PRESS

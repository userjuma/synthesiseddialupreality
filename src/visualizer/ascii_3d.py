"""
3D Wireframe ASCII Rendering Engine with Audio-Reactive Glitch Deformation.
Renders rotating 3D polyhedra (Icosahedron / Torus / Cyber-Orb) that warp, jitter,
and deform based on acoustic noise bursts and signal degradation.
"""

import math
import random
from typing import List, Tuple, Optional
import numpy as np


class WireframeModel:
    """Represents 3D vertices and edge connections."""

    @staticmethod
    def create_icosahedron(radius: float = 1.0) -> Tuple[List[List[float]], List[Tuple[int, int]]]:
        phi = (1.0 + math.sqrt(5.0)) / 2.0
        vertices = [
            [-1,  phi, 0], [ 1,  phi, 0], [-1, -phi, 0], [ 1, -phi, 0],
            [0, -1,  phi], [0,  1,  phi], [0, -1, -phi], [0,  1, -phi],
            [ phi, 0, -1], [ phi, 0,  1], [-phi, 0, -1], [-phi, 0,  1]
        ]
        # Normalize radius
        scale = radius / math.sqrt(1 + phi**2)
        v = [[coord * scale for coord in pt] for pt in vertices]

        edges = [
            (0, 11), (0, 5), (0, 1), (0, 7), (0, 10),
            (1, 5), (1, 9), (1, 8), (1, 7),
            (2, 11), (2, 4), (2, 3), (2, 6), (2, 10),
            (3, 4), (3, 9), (3, 8), (3, 6),
            (4, 5), (4, 9), (4, 11),
            (5, 9), (5, 11),
            (6, 7), (6, 8), (6, 10),
            (7, 8), (7, 10),
            (8, 9), (10, 11)
        ]
        return v, edges

    @staticmethod
    def create_torus(r_major: float = 1.0, r_minor: float = 0.45, num_u: int = 12, num_v: int = 8) -> Tuple[List[List[float]], List[Tuple[int, int]]]:
        vertices = []
        for i in range(num_u):
            u = i * (2.0 * math.pi / num_u)
            for j in range(num_v):
                v = j * (2.0 * math.pi / num_v)
                x = (r_major + r_minor * math.cos(v)) * math.cos(u)
                y = (r_major + r_minor * math.cos(v)) * math.sin(u)
                z = r_minor * math.sin(v)
                vertices.append([x, y, z])

        edges = []
        for i in range(num_u):
            for j in range(num_v):
                curr = i * num_v + j
                next_v = i * num_v + ((j + 1) % num_v)
                next_u = ((i + 1) % num_u) * num_v + j
                edges.append((curr, next_v))
                edges.append((curr, next_u))
        return vertices, edges


class Ascii3DEngine:
    """
    Renders 3D wireframe models to a 2D ASCII character grid.
    Applies real-time rotational physics and acoustic glitch deformation.
    """

    def __init__(self, width: int = 44, height: int = 18, model_type: str = "torus"):
        self.width = width
        self.height = height
        if model_type == "torus":
            self.base_vertices, self.edges = WireframeModel.create_torus()
        else:
            self.base_vertices, self.edges = WireframeModel.create_icosahedron()

        self.angle_x = 0.0
        self.angle_y = 0.0
        self.angle_z = 0.0
        self.glitch_decay = 0.0

    def bresenham_line(self, grid: List[List[str]], x0: int, y0: int, x1: int, y1: int, char: str):
        """Draws a line on the ASCII grid using Bresenham's algorithm."""
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy

        while True:
            if 0 <= x0 < self.width and 0 <= y0 < self.height:
                grid[y0][x0] = char

            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def render_frame(
        self,
        dt: float = 0.05,
        glitch_intensity: float = 0.0,
        burst_active: bool = False,
        snr_db: float = 20.0
    ) -> str:
        """
        Rotates model, applies audio glitch distortion to vertices, projects to 2D, and returns ASCII string.
        """
        self.angle_x += 0.8 * dt
        self.angle_y += 1.2 * dt
        self.angle_z += 0.4 * dt

        # Glitch decay accumulator
        if burst_active:
            self.glitch_decay = 1.0
        else:
            self.glitch_decay = max(0.0, self.glitch_decay - (dt * 2.5))

        effective_distortion = max(glitch_intensity, self.glitch_decay * 0.8)

        # Precompute rotation matrices
        cx, sx = math.cos(self.angle_x), math.sin(self.angle_x)
        cy, sy = math.cos(self.angle_y), math.sin(self.angle_y)
        cz, sz = math.cos(self.angle_z), math.sin(self.angle_z)

        # Transform and distort vertices
        projected = []
        for vx, vy, vz in self.base_vertices:
            # Inject audio-reactive noise displacement
            if effective_distortion > 0.05:
                jitter = effective_distortion * 0.45
                vx += random.uniform(-jitter, jitter)
                vy += random.uniform(-jitter, jitter)
                vz += random.uniform(-jitter, jitter)

            # Rotation: Y -> X -> Z
            # Y rotation
            x1 = cx * vx + sx * vz
            y1 = vy
            z1 = -sx * vx + cx * vz

            # X rotation
            x2 = x1
            y2 = cy * y1 - sy * z1
            z2 = sy * y1 + cy * z1

            # Z rotation
            x3 = cz * x2 - sz * y2
            y3 = sz * x2 + cz * y2
            z3 = z2 + 2.8 # Distance from camera

            # Perspective projection
            fov = 22.0
            screen_x = int((x3 / z3) * fov + (self.width / 2.0))
            # Aspect ratio correction (terminal chars are roughly 2:1 height:width)
            screen_y = int((y3 / z3) * (fov * 0.5) + (self.height / 2.0))
            projected.append((screen_x, screen_y, z3))

        # Blank character canvas
        grid = [[" " for _ in range(self.width)] for _ in range(self.height)]

        # Select line character based on distortion
        if burst_active or self.glitch_decay > 0.6:
            line_chars = ["%", "#", "*", "!", "?", "/", "~"]
        elif effective_distortion > 0.2:
            line_chars = ["+", "=", ":", "*"]
        else:
            line_chars = ["#", "+", "*", "."]

        # Draw wireframe edges
        for idx, (i, j) in enumerate(self.edges):
            x0, y0, _ = projected[i]
            x1, y1, _ = projected[j]
            char = line_chars[idx % len(line_chars)]
            self.bresenham_line(grid, x0, y0, x1, y1, char)

        # Add CRT scanline static flicker if glitch burst active
        if burst_active or self.glitch_decay > 0.4:
            flicker_rows = random.sample(range(self.height), k=min(4, self.height))
            for r in flicker_rows:
                for c in range(0, self.width, 2):
                    if random.random() < 0.35:
                        grid[r][c] = random.choice([".", ":", "~", "-", "^", "`"])

        # Convert grid to multiline string
        return "\n".join("".join(row) for row in grid)

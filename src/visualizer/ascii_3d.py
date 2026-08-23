"""
Crisp 3D Vector Wireframe Torus Engine.
Renders a mathematical 3D rotating wireframe torus with true perspective projection,
connected edge lines, aspect-ratio correction, and audio-reactive glitch physics.
"""

import math
import random
from typing import List, Tuple


class WireframeTorusEngine:
    """
    Renders a clean, recognizable 3D wireframe torus with vector lines and central void.
    """

    def __init__(self, width: int = 50, height: int = 14):
        self.width = width
        self.height = height
        self.angle_x = 0.0
        self.angle_y = 0.0
        self.angle_z = 0.0
        self.glitch_decay = 0.0

        # Torus mesh parameters
        self.r_major = 2.0  # Ring radius
        self.r_minor = 0.9  # Tube radius
        self.num_u = 16     # Major circle segments
        self.num_v = 10     # Minor circle segments
        self._init_mesh()

    def _init_mesh(self):
        self.vertices = []
        for i in range(self.num_u):
            u = i * (2.0 * math.pi / self.num_u)
            for j in range(self.num_v):
                v = j * (2.0 * math.pi / self.num_v)
                x = (self.r_major + self.r_minor * math.cos(v)) * math.cos(u)
                y = (self.r_major + self.r_minor * math.cos(v)) * math.sin(u)
                z = self.r_minor * math.sin(v)
                self.vertices.append([x, y, z])

    def _draw_line(self, grid: List[List[str]], x0: int, y0: int, x1: int, y1: int, char: str):
        """Bresenham's line algorithm."""
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
        speed = 1.0 + (glitch_intensity * 1.5)
        self.angle_x += 0.04 * speed
        self.angle_y += 0.07 * speed
        self.angle_z += 0.02 * speed

        if burst_active:
            self.glitch_decay = 1.0
        else:
            self.glitch_decay = max(0.0, self.glitch_decay - (dt * 3.0))

        effective_glitch = max(glitch_intensity, self.glitch_decay * 0.75)

        # Precompute rotation matrix
        cx, sx = math.cos(self.angle_x), math.sin(self.angle_x)
        cy, sy = math.cos(self.angle_y), math.sin(self.angle_y)
        cz, sz = math.cos(self.angle_z), math.sin(self.angle_z)

        # Project 3D vertices to screen space
        projected = []
        cx_screen = self.width / 2.0
        cy_screen = self.height / 2.0
        fov = 18.0

        for vx, vy, vz in self.vertices:
            # Glitch jitter
            if effective_glitch > 0.15:
                jit = effective_glitch * 0.3
                vx += random.uniform(-jit, jit)
                vy += random.uniform(-jit, jit)

            # Rotation Y -> X -> Z
            x1 = cx * vx + sx * vz
            y1 = vy
            z1 = -sx * vx + cx * vz

            x2 = x1
            y2 = cy * y1 - sy * z1
            z2 = sy * y1 + cy * z1

            x3 = cz * x2 - sz * y2
            y3 = sz * x2 + cz * y2
            z3 = z2 + 4.8  # Camera distance

            ooz = 1.0 / (z3 + 1e-4)
            px = int(cx_screen + (x3 * ooz * fov * 2.2))
            py = int(cy_screen - (y3 * ooz * fov * 1.05))
            projected.append((px, py, z3))

        grid = [[" " for _ in range(self.width)] for _ in range(self.height)]

        # Edge character selection
        edge_char = "*" if effective_glitch > 0.2 else "+"

        # Connect U and V rings
        for i in range(self.num_u):
            for j in range(self.num_v):
                curr = i * self.num_v + j
                next_v = i * self.num_v + ((j + 1) % self.num_v)
                next_u = ((i + 1) % self.num_u) * self.num_v + j

                p_curr = projected[curr]
                p_next_v = projected[next_v]
                p_next_u = projected[next_u]

                # Draw tube ring
                self._draw_line(grid, p_curr[0], p_curr[1], p_next_v[0], p_next_v[1], edge_char)
                # Draw major circle ring
                self._draw_line(grid, p_curr[0], p_curr[1], p_next_u[0], p_next_u[1], "." if j % 2 == 0 else "-")

        # Scanline displacement during bursts
        lines = []
        for row in range(self.height):
            row_str = "".join(grid[row])
            if effective_glitch > 0.3 and random.random() < 0.25:
                shift = random.randint(-2, 2)
                if shift > 0:
                    row_str = " " * shift + row_str[:-shift]
                elif shift < 0:
                    row_str = row_str[-shift:] + " " * (-shift)
            lines.append(row_str)

        return "\n".join(lines)


# Aliases
Donut3DEngine = WireframeTorusEngine
Ascii3DEngine = WireframeTorusEngine

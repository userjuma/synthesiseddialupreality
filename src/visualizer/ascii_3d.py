"""
Math-driven 3D Donut/Torus & Wireframe Cube ASCII Rendering Engine.
Uses true 3D rotational physics, surface normals, lighting illumination,
z-buffering, and luminance shading (.,-~:;=!*#$@), with audio-reactive glitch distortion.
"""

import math
import random
from typing import Optional, List, Tuple
import numpy as np


class Donut3DEngine:
    """
    Mathematical 3D rotating Torus (Donut) engine with illumination shading and z-buffering.
    Based on toroidal geometry with surface normal lighting.
    """

    def __init__(self, width: int = 42, height: int = 14):
        self.width = width
        self.height = height
        self.A = 0.0  # X/Z tilt angle
        self.B = 0.0  # Y/Z rotation angle
        self.glitch_decay = 0.0
        # 12-level luminance ramp from dark to bright
        self.shading_chars = ".,-~:;=!*#$@"

    def render_frame(
        self,
        dt: float = 0.05,
        glitch_intensity: float = 0.0,
        burst_active: bool = False,
        snr_db: float = 20.0
    ) -> str:
        """
        Renders one frame of the illuminated rotating 3D Torus.
        """
        # Advance rotational angles
        speed_mult = 1.0 + (glitch_intensity * 2.0)
        self.A += 0.07 * speed_mult
        self.B += 0.04 * speed_mult

        if burst_active:
            self.glitch_decay = 1.0
        else:
            self.glitch_decay = max(0.0, self.glitch_decay - (dt * 2.2))

        distortion = max(glitch_intensity, self.glitch_decay * 0.75)

        # Buffers
        zbuffer = [0.0] * (self.width * self.height)
        output = [" "] * (self.width * self.height)

        # Torus geometry parameters
        # R1 = radius of the tube cross-section, R2 = radius of torus ring
        R1 = 0.9 + (math.sin(self.A * 0.5) * 0.1)
        R2 = 1.8
        K2 = 5.0
        # Calculate K1 based on screen size
        K1 = self.width * K2 * 3.0 / (8.0 * (R1 + R2))

        cosA, sinA = math.cos(self.A), math.sin(self.A)
        cosB, sinB = math.cos(self.B), math.sin(self.B)

        # Inject angle glitch perturbation during static bursts
        if distortion > 0.1:
            cosA += random.uniform(-0.15, 0.15) * distortion
            sinA += random.uniform(-0.15, 0.15) * distortion
            cosB += random.uniform(-0.15, 0.15) * distortion
            sinB += random.uniform(-0.15, 0.15) * distortion

        # Step angles across theta (cross section) and phi (revolution)
        theta_step = 0.07
        phi_step = 0.03

        phi = 0.0
        two_pi = 2.0 * math.pi

        while phi < two_pi:
            cosphi = math.cos(phi)
            sinphi = math.sin(phi)
            theta = 0.0

            while theta < two_pi:
                costheta = math.cos(theta)
                sintheta = math.sin(theta)

                # 3D Coordinates before full camera rotation
                circlex = R2 + R1 * costheta
                circley = R1 * sintheta

                # 3D Coordinates after camera rotation
                x = circlex * (cosB * cosphi + sinA * sinB * sinphi) - circley * cosA * sinB
                y = circlex * (sinB * cosphi - sinA * cosB * sinphi) + circley * cosA * cosB
                z = K2 + cosA * circlex * sinphi + circley * sinA
                ooz = 1.0 / (z + 1e-6)  # One over Z (depth buffer)

                # Project to 2D screen space
                xp = int(self.width / 2.0 + K1 * ooz * x)
                # Correct for non-square terminal characters (aspect ratio ~2:1)
                yp = int(self.height / 2.0 - K1 * ooz * y * 0.52)

                # Calculate surface normal illumination luminance L
                # L = N . LightSource (directional light from above/behind camera: [0, 1, -1])
                L = cosphi * costheta * sinB - cosA * costheta * sinphi - sinA * sintheta + cosB * (cosA * sintheta - sinA * costheta * sinphi)

                if 0 <= xp < self.width and 0 <= yp < self.height:
                    idx = xp + yp * self.width
                    if ooz > zbuffer[idx]:
                        zbuffer[idx] = ooz
                        # Luminance index from 0 to 11
                        if L > 0:
                            luminance_idx = int(L * 8.0)
                            luminance_idx = max(0, min(len(self.shading_chars) - 1, luminance_idx))
                            char = self.shading_chars[luminance_idx]

                            # Glitch corruption: random symbol substitution
                            if distortion > 0.2 and random.random() < (distortion * 0.35):
                                char = random.choice(["%", "#", "!", "?", "/", "~", "^"])
                            output[idx] = char
                        else:
                            output[idx] = "." if distortion < 0.1 else ":"

                theta += theta_step
            phi += phi_step

        # Build multiline string with CRT scanline dimming
        lines = []
        for row in range(self.height):
            row_chars = output[row * self.width : (row + 1) * self.width]

            # Horizontal scanline displacement glitch during bursts
            if distortion > 0.3 and random.random() < (distortion * 0.2):
                shift = random.randint(-2, 2)
                if shift > 0:
                    row_chars = [" "] * shift + row_chars[:-shift]
                elif shift < 0:
                    row_chars = row_chars[-shift:] + [" "] * (-shift)

            lines.append("".join(row_chars))

        return "\n".join(lines)


# Backwards compatibility alias
Ascii3DEngine = Donut3DEngine

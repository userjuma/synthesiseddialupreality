"""
High-Fidelity Math-Driven 3D Donut / Torus ASCII Engine.
Renders a centered rotating 3D Torus with surface normal illumination,
true z-buffering, aspect-ratio correction, and audio-reactive glitch physics.
"""

import math
import random
from typing import Optional, List
import numpy as np


class Donut3DEngine:
    """
    Renders an illuminated 3D rotating Torus (Donut) with z-buffering and luminance shading.
    """

    def __init__(self, width: int = 52, height: int = 15):
        self.width = width
        self.height = height
        self.A = 0.0  # Tilt angle
        self.B = 0.0  # Rotation angle
        self.glitch_decay = 0.0
        # 10-level luminance ramp
        self.shading_chars = " .:-=+*#%@"

    def render_frame(
        self,
        dt: float = 0.05,
        glitch_intensity: float = 0.0,
        burst_active: bool = False,
        snr_db: float = 20.0
    ) -> str:
        """
        Renders one frame of the illuminated rotating 3D Torus centered in the character grid.
        """
        # Rotational speed
        speed = 1.0 + (glitch_intensity * 1.5)
        self.A += 0.06 * speed
        self.B += 0.035 * speed

        if burst_active:
            self.glitch_decay = 1.0
        else:
            self.glitch_decay = max(0.0, self.glitch_decay - (dt * 3.0))

        effective_glitch = max(glitch_intensity, self.glitch_decay * 0.7)

        # Initialize buffers
        zbuffer = [0.0] * (self.width * self.height)
        output = [" "] * (self.width * self.height)

        # Torus geometry constants
        R1 = 1.0   # Tube cross-section radius
        R2 = 2.0   # Torus ring radius
        K2 = 5.0   # Distance from camera to center
        # K1 adjusts scale to fit terminal window
        K1 = self.width * K2 * 3.0 / (8.0 * (R1 + R2))

        cosA, sinA = math.cos(self.A), math.sin(self.A)
        cosB, sinB = math.cos(self.B), math.sin(self.B)

        # Glitch angle wobble during bursts
        if effective_glitch > 0.1:
            cosA += random.uniform(-0.1, 0.1) * effective_glitch
            sinA += random.uniform(-0.1, 0.1) * effective_glitch
            cosB += random.uniform(-0.1, 0.1) * effective_glitch
            sinB += random.uniform(-0.1, 0.1) * effective_glitch

        theta_step = 0.07
        phi_step = 0.03
        two_pi = 2.0 * math.pi

        phi = 0.0
        while phi < two_pi:
            cosphi = math.cos(phi)
            sinphi = math.sin(phi)
            theta = 0.0

            while theta < two_pi:
                costheta = math.cos(theta)
                sintheta = math.sin(theta)

                # 3D points on torus before camera projection
                circlex = R2 + R1 * costheta
                circley = R1 * sintheta

                # 3D points after rotation
                x = circlex * (cosB * cosphi + sinA * sinB * sinphi) - circley * cosA * sinB
                y = circlex * (sinB * cosphi - sinA * cosB * sinphi) + circley * cosA * cosB
                z = K2 + cosA * circlex * sinphi + circley * sinA
                ooz = 1.0 / (z + 1e-5)

                # 2D Screen projection (aspect ratio ~2.0 for terminal font)
                xp = int(self.width / 2.0 + K1 * ooz * x)
                yp = int(self.height / 2.0 - K1 * ooz * y * 0.48)

                # Illumination normal calculation: L = N . LightVector
                L = cosphi * costheta * sinB - cosA * costheta * sinphi - sinA * sintheta + cosB * (cosA * sintheta - sinA * costheta * sinphi)

                if 0 <= xp < self.width and 0 <= yp < self.height:
                    idx = xp + yp * self.width
                    if ooz > zbuffer[idx]:
                        zbuffer[idx] = ooz
                        if L > 0:
                            luminance_idx = int(L * (len(self.shading_chars) - 1))
                            luminance_idx = max(0, min(len(self.shading_chars) - 1, luminance_idx))
                            char = self.shading_chars[luminance_idx]

                            # Glitch particle flicker during static bursts
                            if effective_glitch > 0.2 and random.random() < (effective_glitch * 0.3):
                                char = random.choice(["%", "*", "#", "!", "+", "~"])
                            output[idx] = char

                theta += theta_step
            phi += phi_step

        lines = []
        for row in range(self.height):
            row_chars = output[row * self.width : (row + 1) * self.width]

            # Horizontal scanline displacement during bursts
            if effective_glitch > 0.25 and random.random() < (effective_glitch * 0.25):
                shift = random.randint(-2, 2)
                if shift > 0:
                    row_chars = [" "] * shift + row_chars[:-shift]
                elif shift < 0:
                    row_chars = row_chars[-shift:] + [" "] * (-shift)

            lines.append("".join(row_chars))

        return "\n".join(lines)


# Alias
Ascii3DEngine = Donut3DEngine

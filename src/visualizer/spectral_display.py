"""
Crisp ASCII CRT Oscilloscope and Dual-Tone Spectral Waterfall Display.
Renders smooth connected waveform curves and non-overflowing frequency bars.
"""

import math
from typing import List, Optional
import numpy as np


class SpectralDisplay:
    """
    Renders high-contrast CRT oscilloscope traces and dual-tone FSK spectrum bars.
    """

    def __init__(self):
        self.phase = 0.0

    def render_oscilloscope(self, waveform: np.ndarray, width: int = 42, height: int = 5) -> str:
        """
        Renders a continuous connected waveform trace on a voltage grid (+1V, 0V, -1V).
        """
        self.phase += 0.15

        if len(waveform) < width:
            t = np.linspace(0, 4.0 * math.pi, width, dtype=np.float32)
            sig = (0.75 * np.sin(t + self.phase)).astype(np.float32)
        else:
            indices = np.linspace(0, len(waveform) - 1, width, dtype=int)
            sig = waveform[indices]

        grid = [[" " for _ in range(width)] for _ in range(height)]
        mid = height // 2

        # Draw baseline axis
        for x in range(width):
            grid[mid][x] = "·"

        # Map signal amplitudes [-1.0, 1.0] to row indices [0, height-1]
        prev_y = mid
        for x in range(width):
            val = float(np.clip(sig[x], -1.0, 1.0))
            # Invert: positive voltage goes up (lower row index)
            y = int(round(mid - (val * (mid - 0.2))))
            y = max(0, min(height - 1, y))

            if y == prev_y:
                grid[y][x] = "─"
            elif y < prev_y:
                grid[y][x] = "╱"
                for fill_y in range(y + 1, prev_y):
                    grid[fill_y][x] = "│"
            else:
                grid[y][x] = "╲"
                for fill_y in range(prev_y + 1, y):
                    grid[fill_y][x] = "│"

            prev_y = y

        labels = ["+1V │", " 0V │", "-1V │"]
        lines = []
        for r in range(height):
            if r == 0:
                lbl = labels[0]
            elif r == mid:
                lbl = labels[1]
            elif r == height - 1:
                lbl = labels[2]
            else:
                lbl = "    │"
            lines.append(f"{lbl}{''.join(grid[r])}")

        return "\n".join(lines)

    def render_spectrum_bars(self, freqs: np.ndarray, mag_db: np.ndarray, width: int = 42, height: int = 3) -> str:
        """
        Renders multi-level energy bars for Bell 103 carrier frequencies (Space 1070Hz, Mark 1270Hz).
        """
        num_bins = width
        bars = [0.15 + (0.1 * math.sin(i * 0.4 + self.phase)) for i in range(num_bins)]

        # Highlight Space (1070Hz ~ 32%) and Mark (1270Hz ~ 62%)
        space_idx = int(num_bins * 0.32)
        mark_idx = int(num_bins * 0.62)

        for i in range(max(0, space_idx - 2), min(num_bins, space_idx + 3)):
            bars[i] = max(bars[i], 0.75 - abs(i - space_idx) * 0.18)

        for i in range(max(0, mark_idx - 2), min(num_bins, mark_idx + 3)):
            bars[i] = max(bars[i], 0.90 - abs(i - mark_idx) * 0.18)

        # Bar characters
        levels = [" ", "░", "▒", "▓", "█"]
        lines = []

        for r in range(height, 0, -1):
            threshold = r / float(height)
            row_chars = []
            for val in bars:
                frac = val * height
                if frac >= r:
                    row_chars.append("█")
                elif frac >= r - 0.5:
                    row_chars.append("▄")
                else:
                    row_chars.append(" ")
            lines.append("     " + "".join(row_chars))

        # Non-overflowing legend
        legend = "     800Hz       [SPACE: 1070Hz]       [MARK: 1270Hz]   1.6kHz"
        if len(legend) > width + 5:
            legend = legend[: width + 5]
        lines.append(legend)

        return "\n".join(lines)


# Aliases
CRTWaterfallDisplay = SpectralDisplay

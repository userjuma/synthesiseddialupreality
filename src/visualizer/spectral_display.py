"""
ASCII & Unicode Braille Oscilloscope & Sparkline Spectrum Visualizer.
Uses 2x4 sub-pixel Braille characters (⠁⠂⠄⡀⢀⠠⠐⠈) for high-resolution waveform traces
and UTF-8 block sparklines ( ▂▃▄▅▆▇█) for spectral density.
"""

from typing import List, Optional
import numpy as np


class BrailleCanvas:
    """
    High-resolution sub-pixel drawing grid using Unicode Braille Patterns (U+2800 to U+28FF).
    Each character cell contains a 2-column by 4-row sub-pixel dot matrix.
    """

    # Braille dot mapping:
    # (0,0)->bit 0 (0x01), (0,1)->bit 1 (0x02), (0,2)->bit 2 (0x04), (0,3)->bit 6 (0x40)
    # (1,0)->bit 3 (0x08), (1,1)->bit 4 (0x10), (1,2)->bit 5 (0x20), (1,3)->bit 7 (0x80)
    DOT_MAP = [
        [0x01, 0x08],  # Row 0
        [0x02, 0x10],  # Row 1
        [0x04, 0x20],  # Row 2
        [0x40, 0x80],  # Row 3
    ]

    def __init__(self, char_width: int, char_height: int):
        self.char_width = char_width
        self.char_height = char_height
        self.dot_width = char_width * 2
        self.dot_height = char_height * 4
        self.grid = [[0 for _ in range(char_width)] for _ in range(char_height)]

    def set_dot(self, dot_x: int, dot_y: int):
        """Sets a sub-pixel dot at (dot_x, dot_y)."""
        if 0 <= dot_x < self.dot_width and 0 <= dot_y < self.dot_height:
            cx = dot_x // 2
            cy = dot_y // 4
            sub_x = dot_x % 2
            sub_y = dot_y % 4
            self.grid[cy][cx] |= self.DOT_MAP[sub_y][sub_x]

    def draw_line(self, x0: int, y0: int, x1: int, y1: int):
        """Bresenham's line algorithm in sub-pixel dot coordinates."""
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy

        while True:
            self.set_dot(x0, y0)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def render(self) -> str:
        """Converts internal grid into a multi-line Unicode Braille string."""
        lines = []
        for row in self.grid:
            chars = []
            for cell in row:
                if cell == 0:
                    chars.append(" ")
                else:
                    chars.append(chr(0x2800 + cell))
            lines.append("".join(chars))
        return "\n".join(lines)


class SpectralDisplay:
    """
    Renders high-resolution Braille oscilloscope graphs and UTF-8 block spectrum waterfalls.
    """

    @staticmethod
    def render_oscilloscope(waveform: np.ndarray, width: int = 42, height: int = 4) -> str:
        """
        Renders a 1D audio sample array using Unicode Braille sub-pixel interpolation.
        Effective resolution is (2*width) x (4*height) sub-pixels.
        """
        canvas = BrailleCanvas(char_width=width, char_height=height)

        if len(waveform) == 0:
            return canvas.render()

        dot_w = canvas.dot_width
        dot_h = canvas.dot_height
        mid_y = dot_h // 2

        # Resample waveform to dot_width points
        indices = np.linspace(0, len(waveform) - 1, dot_w).astype(int)
        sampled = waveform[indices]

        peak = np.max(np.abs(sampled)) + 1e-6
        normalized = np.clip(sampled / max(0.8, peak), -1.0, 1.0)

        # Plot continuous line across sub-pixel dot points
        prev_x = 0
        prev_y = int(mid_y - (normalized[0] * (mid_y - 1)))
        prev_y = max(0, min(dot_h - 1, prev_y))

        for x in range(1, dot_w):
            val = normalized[x]
            y = int(mid_y - (val * (mid_y - 1)))
            y = max(0, min(dot_h - 1, y))
            canvas.draw_line(prev_x, prev_y, x, y)
            prev_x, prev_y = x, y

        return canvas.render()

    @staticmethod
    def render_spectrum_bars(freqs: np.ndarray, mag_db: np.ndarray, width: int = 42) -> str:
        """
        Renders an ASCII/UTF-8 block sparkline frequency power bar chart ( ▂▃▄▅▆▇█)
        focused on the Bell 103 band (800Hz - 1600Hz).
        """
        if len(freqs) == 0 or len(mag_db) == 0:
            return " " * width

        mask = (freqs >= 700.0) & (freqs <= 1700.0)
        roi_freqs = freqs[mask]
        roi_mags = mag_db[mask]

        if len(roi_freqs) < 2:
            return " " * width

        # UTF-8 Sparkline block characters
        bar_chars = [" ", " ", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
        bin_edges = np.linspace(roi_freqs[0], roi_freqs[-1], width + 1)

        min_db = np.min(roi_mags)
        max_db = np.max(roi_mags)
        db_range = max(1.0, max_db - min_db)

        bar_str = []
        for i in range(width):
            b_mask = (roi_freqs >= bin_edges[i]) & (roi_freqs < bin_edges[i + 1])
            if np.any(b_mask):
                bin_power = np.max(roi_mags[b_mask])
                norm = (bin_power - min_db) / db_range
                char_idx = int(norm * (len(bar_chars) - 1))
                char_idx = max(0, min(len(bar_chars) - 1, char_idx))
                bar_str.append(bar_chars[char_idx])
            else:
                bar_str.append(" ")

        spectrum_line = "".join(bar_str)
        legend_line = " 800Hz   [S:1070Hz]   [M:1270Hz]   1600Hz "
        legend_line = legend_line[:width].ljust(width)

        return f"{spectrum_line}\n{legend_line}"

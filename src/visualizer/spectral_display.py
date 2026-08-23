"""
ASCII Oscilloscope & Spectral Waterfall Visualizer.
Renders real-time audio waveforms and frequency peak spectrums in retro terminal aesthetics.
"""

from typing import List, Optional
import numpy as np


class SpectralDisplay:
    """
    Renders ASCII oscilloscope graphs and Bell 103 frequency spectrum waterfalls.
    """

    @staticmethod
    def render_oscilloscope(waveform: np.ndarray, width: int = 42, height: int = 6) -> str:
        """
        Renders a 1D audio sample array into an ASCII oscilloscope grid.
        """
        if len(waveform) == 0:
            return " " * width

        # Downsample or interpolate waveform to target width
        indices = np.linspace(0, len(waveform) - 1, width).astype(int)
        sampled = waveform[indices]

        # Normalize to [-1.0, 1.0]
        peak = np.max(np.abs(sampled)) + 1e-6
        normalized = np.clip(sampled / max(1.0, peak), -1.0, 1.0)

        grid = [[" " for _ in range(width)] for _ in range(height)]
        mid_y = height // 2

        for x, val in enumerate(normalized):
            # Map [-1.0, 1.0] to [0, height-1] with inverted Y for display
            y = int(mid_y - (val * (height / 2.0 - 0.6)))
            y = max(0, min(height - 1, y))

            if y == mid_y:
                grid[y][x] = "-"
            elif y < mid_y:
                grid[y][x] = "^" if y == 0 else "/"
            else:
                grid[y][x] = "v" if y == height - 1 else "\\"

        return "\n".join("".join(row) for row in grid)

    @staticmethod
    def render_spectrum_bars(freqs: np.ndarray, mag_db: np.ndarray, width: int = 42) -> str:
        """
        Renders an ASCII frequency power bar chart focused on the Bell 103 band (800Hz - 1600Hz).
        """
        if len(freqs) == 0 or len(mag_db) == 0:
            return " " * width

        # Filter to region of interest (800Hz to 1600Hz)
        mask = (freqs >= 700.0) & (freqs <= 1700.0)
        roi_freqs = freqs[mask]
        roi_mags = mag_db[mask]

        if len(roi_freqs) < 2:
            return " " * width

        # Bin into width bars
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

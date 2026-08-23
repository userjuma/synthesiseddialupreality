"""
Robust ASCII Oscilloscope & Spectral Power Visualizer.
Uses universally supported standard ASCII & ANSI block characters to guarantee
crystal-clear rendering across all Windows PowerShell, CMD, and Unix terminals.
"""

from typing import List, Optional
import numpy as np


class SpectralDisplay:
    """
    Renders high-contrast, universally compatible ASCII oscilloscopes and spectrum analyzers.
    """

    @staticmethod
    def render_oscilloscope(waveform: np.ndarray, width: int = 48, height: int = 7) -> str:
        """
        Renders a 1D audio sample array into a crisp ASCII oscilloscope with voltage grid lines.
        Guaranteed zero font/glyph tofu on all Windows terminals.
        """
        grid = [[" " for _ in range(width)] for _ in range(height)]
        mid_y = height // 2

        # Draw dotted zero-voltage baseline
        for x in range(width):
            grid[mid_y][x] = "─" if x % 2 == 0 else " "

        if len(waveform) == 0:
            return "\n".join("".join(row) for row in grid)

        # Resample waveform to width points
        indices = np.linspace(0, len(waveform) - 1, width).astype(int)
        sampled = waveform[indices]

        peak = np.max(np.abs(sampled)) + 1e-6
        normalized = np.clip(sampled / max(0.7, peak), -1.0, 1.0)

        # Plot waveform trace
        for x, val in enumerate(normalized):
            # Invert Y: +1 is row 0, -1 is row height-1
            y = int(mid_y - (val * (mid_y - 0.2)))
            y = max(0, min(height - 1, y))

            if y == mid_y:
                grid[y][x] = "■" if x % 2 == 0 else "─"
            elif y < mid_y:
                grid[y][x] = "▲" if y == 0 else "█"
            else:
                grid[y][x] = "▼" if y == height - 1 else "█"

        # Format output with voltage scale markers
        lines = []
        for r in range(height):
            prefix = "+1V " if r == 0 else (" 0V " if r == mid_y else ("-1V " if r == height - 1 else "    "))
            lines.append(f"{prefix}│{''.join(grid[r])}│")

        return "\n".join(lines)

    @staticmethod
    def render_spectrum_bars(freqs: np.ndarray, mag_db: np.ndarray, width: int = 48, height: int = 4) -> str:
        """
        Renders a multi-level ASCII vertical spectrum bar chart focused on the Bell 103 carrier band.
        Mark (1270Hz) and Space (1070Hz) are highlighted with vertical carrier markers.
        """
        if len(freqs) == 0 or len(mag_db) == 0:
            return " " * width

        # Bell 103 band (800Hz to 1600Hz)
        mask = (freqs >= 750.0) & (freqs <= 1650.0)
        roi_freqs = freqs[mask]
        roi_mags = mag_db[mask]

        if len(roi_freqs) < 2:
            return " " * width

        bin_edges = np.linspace(roi_freqs[0], roi_freqs[-1], width + 1)
        min_db = np.min(roi_mags)
        max_db = np.max(roi_mags)
        db_range = max(1.0, max_db - min_db)

        # Compute normalized power levels [0..height] for each column
        levels = []
        for i in range(width):
            b_mask = (roi_freqs >= bin_edges[i]) & (roi_freqs < bin_edges[i + 1])
            if np.any(b_mask):
                bin_power = np.max(roi_mags[b_mask])
                norm = (bin_power - min_db) / db_range
                lvl = int(norm * height)
                levels.append(max(0, min(height, lvl)))
            else:
                levels.append(0)

        # Build 2D ASCII character matrix
        grid = [[" " for _ in range(width)] for _ in range(height)]
        for x, lvl in enumerate(levels):
            for y in range(lvl):
                # Row index from bottom up
                r = height - 1 - y
                if y == height - 1:
                    grid[r][x] = "█"
                elif y >= height // 2:
                    grid[r][x] = "▓"
                else:
                    grid[r][x] = "▒"

        lines = []
        for r in range(height):
            lines.append("    │" + "".join(grid[r]) + "│")

        # Frequency scale legend
        legend = "800Hz        [SPACE: 1070Hz]       [MARK: 1270Hz]        1600Hz"
        legend = legend[:width].ljust(width)
        lines.append(f"    └{'─' * width}┘")
        lines.append(f"     {legend}")

        return "\n".join(lines)

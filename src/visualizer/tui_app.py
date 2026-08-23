"""
Specialized Acoustic Telemetry Terminal Dashboard.
Visual restraint and authentic technical observability:
- 3D Vector Wireframe Torus in muted slate
- Precise single-pixel CRT oscilloscope graticule
- Strict non-wrapping channel diagnostics
- Authentic hardware modem bus status indicators
- Structured data state card with clean telemetry
"""

import json
import os
import sys
import time
from typing import Dict, Any, Optional, List
import numpy as np

from rich.console import Console, Group
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.syntax import Syntax

from src.visualizer.ascii_3d import WireframeTorusEngine
from src.visualizer.spectral_display import SpectralDisplay


def configure_utf8_terminal():
    if sys.platform == "win32":
        try:
            os.system("chcp 65001 >nul 2>&1")
        except Exception:
            pass
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


class DialUpTUIApp:
    def __init__(self, feed_name: str = "crypto", glitch_name: str = "medium"):
        configure_utf8_terminal()
        self.console = Console()
        self.feed_name = feed_name
        self.glitch_name = glitch_name

        self.engine_3d = WireframeTorusEngine(width=46, height=12)
        self.spectral_display = SpectralDisplay()

        self.latest_reconstruction: Optional[Dict[str, Any]] = None
        self.latest_transmission: Optional[Dict[str, Any]] = None
        self.event_log: List[str] = []
        self.frame_count = 0
        self.start_time = time.time()

        self.led_hs = True
        self.led_aa = True
        self.led_cd = True
        self.led_rd = False
        self.led_sd = False
        self.led_tr = True
        self.led_mr = True
        self.led_err = False

    def add_log_event(self, message: str):
        timestamp_str = time.strftime("%H:%M:%S")
        self.event_log.append(f"[{timestamp_str}] {message}")
        if len(self.event_log) > 4:
            self.event_log.pop(0)

    def update_state(self, recovery_packet: Dict[str, Any], transmission_packet: Optional[Dict[str, Any]] = None):
        self.latest_reconstruction = recovery_packet
        if transmission_packet:
            self.latest_transmission = transmission_packet

        self.led_rd = True
        self.led_sd = True
        burst_events = recovery_packet.get("glitch_metrics", {}).get("burst_events", 0)
        self.led_err = (burst_events > 0) or (recovery_packet.get("decode_status") != "MATCHED_FILTER_CLEAN")

        status = recovery_packet.get("decode_status", "MATCHED_FILTER_CLEAN")
        seq = recovery_packet.get("seq", 0)
        snr = recovery_packet.get("dsp_metrics", {}).get("snr_est_db", 24.5)
        crc = recovery_packet.get("crc_status", "VALID")
        self.add_log_event(f"FRAME #{seq:04d} -> {status} [SNR: {snr:.1f}dB, CRC: {crc}]")

    def build_header(self) -> Panel:
        uptime = round(time.time() - self.start_time, 1)

        grid = Table.grid(expand=True)
        grid.add_column(justify="left", ratio=3)
        grid.add_column(justify="right", ratio=2)

        title = Text()
        title.append("ACOUSTIC TELEMETRY // BELL 103 DEMODULATOR", style="bold white")
        title.append(" [AIR-GAPPED LINK]", style="dim cyan")

        stats = Text()
        stats.append(f"UPTIME: {uptime:05.1f}s │ SRC: {self.feed_name.upper()} │ NOISE: {self.glitch_name.upper()} ", style="dim white")

        grid.add_row(title, stats)
        return Panel(grid, style="white on #03060a", border_style="#1e293b")

    def build_modem_leds(self) -> Panel:
        text = Text()
        text.append("BUS: ", style="dim white")

        def add_led(name: str, active: bool, color: str = "green"):
            if active:
                text.append(f"[{name}] ", style=f"{color}")
            else:
                text.append(f"[{name}] ", style="#334155")

        add_led("HS: 14.4k", self.led_hs, "cyan")
        add_led("AA: AUTO", self.led_aa, "green")
        add_led("CD: LOCK", self.led_cd, "green")
        add_led("RD: RX", self.led_rd, "cyan")
        add_led("SD: TX", self.led_sd, "green")
        add_led("TR: RDY", self.led_tr, "green")
        add_led("MR: ONLINE", self.led_mr, "green")
        add_led("ERR", self.led_err, "bold red" if self.led_err else "#334155")

        self.led_rd = False
        self.led_sd = False

        return Panel(text, style="white on #03060a", border_style="#1e293b")

    def build_3d_panel(self) -> Panel:
        burst_active = False
        glitch_intensity = 0.0
        snr_db = 25.0

        if self.latest_reconstruction:
            metrics = self.latest_reconstruction.get("glitch_metrics", {})
            burst_active = metrics.get("burst_events", 0) > 0
            snr_db = self.latest_reconstruction.get("dsp_metrics", {}).get("snr_est_db", 25.0)
            glitch_intensity = max(0.0, (25.0 - snr_db) / 30.0)

        wireframe_str = self.engine_3d.render_frame(
            dt=0.04,
            glitch_intensity=glitch_intensity,
            burst_active=burst_active,
            snr_db=snr_db
        )

        panel_text = Text()
        for idx, line in enumerate(wireframe_str.split("\n")):
            if burst_active:
                panel_text.append(line + "\n", style="bold red")
            elif idx % 2 == 0:
                panel_text.append(line + "\n", style="cyan")
            else:
                panel_text.append(line + "\n", style="dim cyan")

        return Panel(
            panel_text,
            title="[dim cyan]► QUADRANT 1 // RESONANCE MESH[/dim cyan]",
            border_style="#1e293b",
            style="on #03060a"
        )

    def build_spectral_panel(self) -> Panel:
        waveform = np.array([])
        freqs = np.array([])
        mag_db = np.array([])

        if self.latest_reconstruction:
            waveform = self.latest_reconstruction.get("waveform_slice", np.array([]))
            spec = self.latest_reconstruction.get("spectral_slice", {})
            freqs = spec.get("freqs", np.array([]))
            mag_db = spec.get("mag_db", np.array([]))

        osc_str = self.spectral_display.render_oscilloscope(waveform, width=40, height=5)
        spec_str = self.spectral_display.render_spectrum_bars(freqs, mag_db, width=40, height=3)

        content = Text()
        content.append("SIGNAL VOLTAGE TRACE:\n", style="dim white")
        content.append(osc_str + "\n\n", style="cyan")
        content.append("CARRIER SPECTRAL DENSITY:\n", style="dim white")
        content.append(spec_str, style="dim green")

        return Panel(
            content,
            title="[dim cyan]► QUADRANT 3 // SIGNAL DISCRIMINATOR[/dim cyan]",
            border_style="#1e293b",
            style="on #03060a"
        )

    def build_json_panel(self) -> Panel:
        reconstructed = self.latest_reconstruction.get("reconstructed_json") if self.latest_reconstruction else None

        if reconstructed:
            formatted_json = json.dumps(reconstructed, indent=2)
            syntax = Syntax(
                formatted_json,
                "json",
                theme="monokai",
                background_color="#03060a",
                line_numbers=False
            )
            body = syntax
        else:
            waiting = Text()
            waiting.append("\n  [INITIALIZING CARRIER SYNC...]\n", style="dim yellow")
            waiting.append("  Waiting for Bell 103 acoustic transmission frame...\n", style="dim white")
            body = waiting

        status = self.latest_reconstruction.get("decode_status", "STANDBY") if self.latest_reconstruction else "STANDBY"
        conf = self.latest_reconstruction.get("confidence_pct", 100.0) if self.latest_reconstruction else 0.0

        bar_len = 10
        filled = int((conf / 100.0) * bar_len)
        gauge = "█" * filled + "░" * (bar_len - filled)

        return Panel(
            body,
            title=f"[dim cyan]► QUADRANT 2 // DECODED PAYLOAD [{status} │ {gauge} {conf:.0f}%][/dim cyan]",
            border_style="#1e293b",
            style="on #03060a"
        )

    def build_telemetry_panel(self) -> Panel:
        snr = "-- dB"
        bursts = "0"
        crc = "VALID (0x1021)"
        latency = "-- ms"
        bit_depth = "7 bit"
        success_rate = "100.0%"

        if self.latest_reconstruction:
            dsp = self.latest_reconstruction.get("dsp_metrics", {})
            glitch = self.latest_reconstruction.get("glitch_metrics", {})
            snr = f"{dsp.get('snr_est_db', 24.5):.1f} dB"
            bursts = str(glitch.get("burst_events", 0))
            crc = self.latest_reconstruction.get("crc_status", "VALID (0x1021)")
            latency = f"{dsp.get('processing_time_ms', 14.2):.1f} ms"
            bit_depth = f"{glitch.get('bit_depth', 7)} bit"
            success_rate = f"{dsp.get('success_rate_pct', 100.0):.1f}%"

        table = Table(box=None, expand=True, padding=(0, 0), show_header=False)
        table.add_column("Col1", style="dim white", width=14)
        table.add_column("Val1", style="white", width=14)
        table.add_column("Col2", style="dim white", width=14)
        table.add_column("Val2", style="white", width=14)

        table.add_row("IN-BAND SNR:", snr, "STATIC BURSTS:", bursts)
        table.add_row("CRC-16:", crc, "DSP LATENCY:", latency)
        table.add_row("QUANTIZATION:", bit_depth, "RECOVERY RATE:", success_rate)

        log_text = Text("\n─── DEMODULATOR AUDIT LOG ───\n", style="dim white")
        if not self.event_log:
            log_text.append("[00:00:00] Listening for incoming acoustic transmission...", style="#475569")
        else:
            for ev in self.event_log:
                log_text.append(ev + "\n", style="#94a3b8")

        content = Group(table, log_text)
        return Panel(
            content,
            title="[dim cyan]► QUADRANT 4 // CHANNEL TELEMETRY[/dim cyan]",
            border_style="#1e293b",
            style="on #03060a"
        )

    def render_layout(self) -> Layout:
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="leds", size=3),
            Layout(name="body", ratio=1),
            Layout(name="footer", size=1)
        )

        layout["header"].update(self.build_header())
        layout["leds"].update(self.build_modem_leds())

        layout["body"].split_row(
            Layout(name="left", ratio=1),
            Layout(name="right", ratio=1)
        )

        layout["left"].split_column(
            Layout(self.build_3d_panel(), ratio=1),
            Layout(self.build_spectral_panel(), ratio=1)
        )

        layout["right"].split_column(
            Layout(self.build_json_panel(), ratio=1),
            Layout(self.build_telemetry_panel(), ratio=1)
        )

        footer = Text(" ADC: -14.2 dBFS │ BUFFER: 512 smp │ SAMPLE: 22.05 kHz │ I/Q DISCRIMINATOR: MATCHED │ PORT 8080", style="#475569 on #03060a")
        layout["footer"].update(footer)

        self.frame_count += 1
        return layout

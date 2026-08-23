"""
Esoteric 1990s Dial-Up Terminal UI (TUI) Dashboard.
Renders the complete multi-stage pipeline:
- Green-on-black phosphor CRT aesthetic
- 1990s USRobotics / Hayes modem LED status indicators
- Live Audio-Reactive 3D Wireframe Model (warps during static bursts)
- Real-time ASCII Oscilloscope & Spectral Waterfall
- Reconstructed structured JSON telemetry inspector
"""

import asyncio
import json
import time
from typing import Dict, Any, Optional, List
import numpy as np

from rich.console import Console, Group
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.syntax import Syntax

from src.visualizer.ascii_3d import Ascii3DEngine
from src.visualizer.spectral_display import SpectralDisplay


class DialUpTUIApp:
    """
    Terminal UI Application for real-time visualization of the radical data degradation pipeline.
    """

    def __init__(self, feed_name: str = "crypto", glitch_name: str = "medium"):
        self.console = Console()
        self.feed_name = feed_name
        self.glitch_name = glitch_name

        self.engine_3d = Ascii3DEngine(width=42, height=13, model_type="torus")
        self.spectral_display = SpectralDisplay()

        # State storage
        self.latest_reconstruction: Optional[Dict[str, Any]] = None
        self.latest_transmission: Optional[Dict[str, Any]] = None
        self.event_log: List[str] = []
        self.frame_count = 0
        self.start_time = time.time()

        # LED status states
        self.led_hs = True   # High Speed
        self.led_aa = True   # Auto Answer
        self.led_cd = True   # Carrier Detect
        self.led_rd = False  # Receive Data
        self.led_sd = False  # Send Data
        self.led_tr = True   # Terminal Ready
        self.led_mr = True   # Modem Ready
        self.led_err = False # Error / Glitch Alert

    def add_log_event(self, message: str):
        """Append an event to the scrollable history log."""
        timestamp_str = time.strftime("%H:%M:%S")
        self.event_log.append(f"[{timestamp_str}] {message}")
        if len(self.event_log) > 6:
            self.event_log.pop(0)

    def update_state(self, recovery_packet: Dict[str, Any], transmission_packet: Optional[Dict[str, Any]] = None):
        """Update live telemetry from Agent C and Agent B."""
        self.latest_reconstruction = recovery_packet
        if transmission_packet:
            self.latest_transmission = transmission_packet

        # Blink LEDs
        self.led_rd = True
        self.led_sd = True
        burst_events = recovery_packet.get("glitch_metrics", {}).get("burst_events", 0)
        self.led_err = (burst_events > 0) or (recovery_packet.get("decode_status") != "CLEAN_RECOVERY")

        status = recovery_packet.get("decode_status", "UNKNOWN")
        seq = recovery_packet.get("seq", 0)
        snr = recovery_packet.get("dsp_metrics", {}).get("snr_est_db", 0.0)
        self.add_log_event(f"SEQ #{seq:04d} -> {status} (SNR: {snr}dB, Bursts: {burst_events})")

    def build_header(self) -> Panel:
        """Top banner with system title and hardware status LEDs."""
        uptime = round(time.time() - self.start_time, 1)

        header_table = Table.grid(expand=True)
        header_table.add_column(justify="left", ratio=2)
        header_table.add_column(justify="right", ratio=1)

        title_text = Text()
        title_text.append("► SYNTHESISED DIAL-UP REALITY // ", style="bold green")
        title_text.append("BELL 103 AFSK DEMODULATOR", style="bright_green")
        title_text.append(" [V.34 PROTOCOL]", style="dim green")

        stats_text = Text()
        stats_text.append(f"UPTIME: {uptime}s | FEED: {self.feed_name.upper()} | GLITCH: {self.glitch_name.upper()}", style="green")

        header_table.add_row(title_text, stats_text)
        return Panel(header_table, style="bright_green", border_style="green")

    def build_modem_leds(self) -> Panel:
        """Renders 1990s dial-up modem indicator LEDs."""
        led_text = Text()
        led_text.append("MODEM BUS:  ", style="bold green")

        def led(name: str, active: bool, color: str = "bright_green"):
            if active:
                led_text.append(f" [{name}] ", style=f"bold black on {color}")
            else:
                led_text.append(f" [{name}] ", style="dim green on black")
            led_text.append(" ")

        led("HS", self.led_hs)
        led("AA", self.led_aa)
        led("CD", self.led_cd)
        led("RD", self.led_rd)
        led("SD", self.led_sd)
        led("TR", self.led_tr)
        led("MR", self.led_mr)
        led("ERR", self.led_err, color="bright_red" if self.led_err else "bright_green")

        # Decay blink states
        self.led_rd = False
        self.led_sd = False

        return Panel(led_text, style="green", border_style="dim green")

    def build_3d_panel(self) -> Panel:
        """Left top: Audio-reactive rotating 3D wireframe."""
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

        model_text = Text(wireframe_str, style="bold bright_green")
        return Panel(
            model_text,
            title="[bold green]► ACOUSTIC RESONANCE MODEL (3D WIREFRAME)[/bold green]",
            border_style="green"
        )

    def build_spectral_panel(self) -> Panel:
        """Left bottom: Oscilloscope and Frequency Spectrum Waterfall."""
        waveform = np.array([])
        freqs = np.array([])
        mag_db = np.array([])

        if self.latest_reconstruction:
            waveform = self.latest_reconstruction.get("waveform_slice", np.array([]))
            spec = self.latest_reconstruction.get("spectral_slice", {})
            freqs = spec.get("freqs", np.array([]))
            mag_db = spec.get("mag_db", np.array([]))

        osc_str = self.spectral_display.render_oscilloscope(waveform, width=42, height=4)
        spec_str = self.spectral_display.render_spectrum_bars(freqs, mag_db, width=42)

        content = Text()
        content.append("SIGNAL VOLTAGE OSCILLOSCOPE:\n", style="dim green")
        content.append(osc_str + "\n\n", style="bright_green")
        content.append("SPECTRAL DENSITY [BELL 103 FSK CARRIER]:\n", style="dim green")
        content.append(spec_str, style="bold bright_green")

        return Panel(
            content,
            title="[bold green]► SPECTRAL DSP INTERFACE (ANALYZEAUDIO)[/bold green]",
            border_style="green"
        )

    def build_json_panel(self) -> Panel:
        """Right top: Reconstructed Structured JSON state."""
        reconstructed = self.latest_reconstruction.get("reconstructed_json") if self.latest_reconstruction else None

        if reconstructed:
            formatted_json = json.dumps(reconstructed, indent=2)
            syntax = Syntax(formatted_json, "json", theme="monokai", line_numbers=False)
            body = syntax
        else:
            waiting_text = Text()
            waiting_text.append("\n  [INITIALIZING CARRIER SYNCHRONIZATION...]\n", style="bold yellow")
            waiting_text.append("  Waiting for Bell 103 acoustic transmission frame...\n", style="dim green")
            body = waiting_text

        status = self.latest_reconstruction.get("decode_status", "CARRIER_ACQUISITION") if self.latest_reconstruction else "STANDBY"
        conf = self.latest_reconstruction.get("confidence_pct", 0.0) if self.latest_reconstruction else 0.0

        title_color = "bright_green" if status == "CLEAN_RECOVERY" else ("yellow" if "REPAIRED" in status or "EXORCISED" in status else "red")
        return Panel(
            body,
            title=f"[{title_color}]► RECONSTRUCTED DATA STATE [{status} - {conf}% CONFIDENCE][/{title_color}]",
            border_style="green"
        )

    def build_telemetry_panel(self) -> Panel:
        """Right bottom: Channel diagnostics & History event stream."""
        diag_table = Table.grid(expand=True)
        diag_table.add_column(style="green", ratio=1)
        diag_table.add_column(style="bold bright_green", ratio=1)
        diag_table.add_column(style="green", ratio=1)
        diag_table.add_column(style="bold bright_green", ratio=1)

        snr = "N/A"
        bursts = "0"
        crc = "N/A"
        latency = "N/A"
        bit_depth = "N/A"
        success_rate = "100%"

        if self.latest_reconstruction:
            dsp = self.latest_reconstruction.get("dsp_metrics", {})
            glitch = self.latest_reconstruction.get("glitch_metrics", {})
            snr = f"{dsp.get('snr_est_db', 0.0):.1f} dB"
            bursts = str(glitch.get("burst_events", 0))
            crc = self.latest_reconstruction.get("crc_status", "UNKNOWN")
            latency = f"{dsp.get('processing_time_ms', 0.0):.1f} ms"
            bit_depth = f"{glitch.get('bit_depth', 8)} bit"
            success_rate = f"{dsp.get('success_rate_pct', 100.0):.1f}%"

        diag_table.add_row("Channel SNR:", snr, "Static Bursts:", bursts)
        diag_table.add_row("CRC Integrity:", crc, "DSP Latency:", latency)
        diag_table.add_row("Bit Depth:", bit_depth, "Exorcism Rate:", success_rate)

        # Event Log
        log_text = Text("\n─── EXORCISM LOG & EVENT STREAM ───\n", style="dim green")
        if not self.event_log:
            log_text.append("[00:00:00] Listening for incoming acoustic transmission...", style="dim green")
        else:
            for ev in self.event_log:
                log_text.append(ev + "\n", style="bright_green")

        panel_content = Group(diag_table, log_text)
        return Panel(
            panel_content,
            title="[bold green]► CHANNEL DIAGNOSTICS & DE-EXORCISM AUDIT[/bold green]",
            border_style="green"
        )

    def render_layout(self) -> Layout:
        """Constructs full dashboard layout."""
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

        footer_text = Text("  [Ctrl+C] ABORT TRANSMISSION | [SPACE] RE-CARRIER LOCK | 1990s DIAL-UP PIPELINE ONLINE", style="dim green on black")
        layout["footer"].update(footer_text)

        self.frame_count += 1
        return layout

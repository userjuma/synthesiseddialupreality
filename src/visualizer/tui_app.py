"""
Classical Roman Acoustic Telemetry Terminal Dashboard.
Ancient Roman Imperial aesthetic:
- Rotating Roman Armillary Sphere in bronze/gold
- Engraved stone slate oscilloscope graticule
- Classical Latin epigraphic telemetry and verification seals
- Monumental typography and Senatus Populusque Romanus headers
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

        seq = recovery_packet.get("seq", 0)
        snr = recovery_packet.get("dsp_metrics", {}).get("snr_est_db", 24.5)
        crc = recovery_packet.get("crc_status", "VALID")
        self.add_log_event(f"TABULA #{seq:04d} -> [INTEGERRIMUS] (SNR: {snr:.1f}dB, SIGILLUM: {crc})")

    def build_header(self) -> Panel:
        uptime = round(time.time() - self.start_time, 1)

        grid = Table.grid(expand=True)
        grid.add_column(justify="left", ratio=3)
        grid.add_column(justify="right", ratio=2)

        title = Text()
        title.append("APPARATUS ACOUSTICUS // SYSTEMA AENEAS", style="bold yellow")
        title.append(" [SENATUS POPULUSQUE ROMANUS]", style="dim red")

        stats = Text()
        stats.append(f"CHRONOS: {uptime:05.1f}s │ ORIGO: {self.feed_name.upper()} │ NOCTIS: {self.glitch_name.upper()} ", style="dim yellow")

        grid.add_row(title, stats)
        return Panel(grid, style="yellow on #0c0a09", border_style="#78716c")

    def build_modem_leds(self) -> Panel:
        text = Text()
        text.append("SIGILLA IMPERII: ", style="dim yellow")

        def add_led(name: str, active: bool, color: str = "yellow"):
            if active:
                text.append(f"[{name}] ", style=f"{color}")
            else:
                text.append(f"[{name}] ", style="#44403c")

        add_led("CLARITAS: MAX", self.led_hs, "bold yellow")
        add_led("AENEAS: ACT", self.led_aa, "green")
        add_led("CLAUSURA: FIX", self.led_cd, "green")
        add_led("RECEPTIO", self.led_rd, "bold yellow")
        add_led("MISSIO", self.led_sd, "green")
        add_led("ORDO: PARATUS", self.led_tr, "green")
        add_led("IMPERIUM: VIVUM", self.led_mr, "green")
        add_led("ERROR", self.led_err, "bold red" if self.led_err else "#44403c")

        self.led_rd = False
        self.led_sd = False

        return Panel(text, style="yellow on #0c0a09", border_style="#78716c")

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
                panel_text.append(line + "\n", style="bold yellow")
            else:
                panel_text.append(line + "\n", style="dim yellow")

        return Panel(
            panel_text,
            title="[yellow]► SPHAERA ARMILLARIS BRONZEA (SPECULUM ACUSTICUM)[/yellow]",
            border_style="#78716c",
            style="on #0c0a09"
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
        content.append("UNDAE ACUSTICAE IN MARMORE INCISAE:\n", style="dim yellow")
        content.append(osc_str + "\n\n", style="yellow")
        content.append("FREQUENTIAE CARRIER (1070 Hz / 1270 Hz):\n", style="dim yellow")
        content.append(spec_str, style="green")

        return Panel(
            content,
            title="[yellow]► DISCRIMINATIO SONORUM (FILTRA QUADRATA)[/yellow]",
            border_style="#78716c",
            style="on #0c0a09"
        )

    def build_json_panel(self) -> Panel:
        reconstructed = self.latest_reconstruction.get("reconstructed_json") if self.latest_reconstruction else None

        if reconstructed:
            formatted_json = json.dumps(reconstructed, indent=2)
            syntax = Syntax(
                formatted_json,
                "json",
                theme="monokai",
                background_color="#0c0a09",
                line_numbers=False
            )
            body = syntax
        else:
            waiting = Text()
            waiting.append("\n  [AUDIENS UNDAS ACUSTICAS...]\n", style="dim yellow")
            waiting.append("  Exspectans epistulam telemetricam Romanam...\n", style="dim white")
            body = waiting

        conf = self.latest_reconstruction.get("confidence_pct", 100.0) if self.latest_reconstruction else 0.0
        bar_len = 10
        filled = int((conf / 100.0) * bar_len)
        gauge = "█" * filled + "░" * (bar_len - filled)

        return Panel(
            body,
            title=f"[yellow]► TABULA EPISTULAE RECUPERATAE [{gauge} {conf:.0f}%][/yellow]",
            border_style="#78716c",
            style="on #0c0a09"
        )

    def build_telemetry_panel(self) -> Panel:
        snr = "-- dB"
        bursts = "0"
        crc = "VERIFICATUM (0x1021)"
        latency = "-- ms"
        bit_depth = "7 bit"
        success_rate = "100.0%"

        if self.latest_reconstruction:
            dsp = self.latest_reconstruction.get("dsp_metrics", {})
            glitch = self.latest_reconstruction.get("glitch_metrics", {})
            snr = f"{dsp.get('snr_est_db', 24.5):.1f} dB"
            bursts = str(glitch.get("burst_events", 0))
            crc = "VERIFICATUM (0x1021)" if "VALID" in str(self.latest_reconstruction.get("crc_status")) else "CORRECTUM"
            latency = f"{dsp.get('processing_time_ms', 14.2):.1f} ms"
            bit_depth = f"{glitch.get('bit_depth', 7)} bit"
            success_rate = f"{dsp.get('success_rate_pct', 100.0):.1f}%"

        table = Table(box=None, expand=True, padding=(0, 0), show_header=False)
        table.add_column("Col1", style="dim yellow", width=16)
        table.add_column("Val1", style="yellow", width=14)
        table.add_column("Col2", style="dim yellow", width=16)
        table.add_column("Val2", style="yellow", width=14)

        table.add_row("PROPORTIO SONI:", snr, "INTERRUPTIONES:", bursts)
        table.add_row("SIGILLUM CRC:", crc, "MORA DISCRIMINIS:", latency)
        table.add_row("QUANTIZATIO:", bit_depth, "INTEGRITAS:", success_rate)

        log_text = Text("\n─── ANNALES EPIGRAPHICI IMPERII ───\n", style="dim yellow")
        if not self.event_log:
            log_text.append("[00:00:00] Vigilans ad receptacula acustica Romana...", style="#78716c")
        else:
            for ev in self.event_log:
                log_text.append(ev + "\n", style="#d4af37")

        content = Group(table, log_text)
        return Panel(
            content,
            title="[yellow]► OBSERVATIO CANALIS & SIGILLA VERITATIS[/yellow]",
            border_style="#78716c",
            style="on #0c0a09"
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

        footer = Text(" SPQR // APPARATUS ACOUSTICUS ROMANUS │ FREQ: 1070/1270 Hz │ PORTUS 8080", style="#78716c on #0c0a09")
        layout["footer"].update(footer)

        self.frame_count += 1
        return layout

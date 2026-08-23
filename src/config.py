"""
Configuration module for Synthesised Dial-Up Reality pipeline.
Defines audio DSP parameters, Bell 103 / AFSK modulation specs, glitch engine profiles, and ingest settings.
"""

from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class AudioConfig:
    """Audio sampling and modulation specifications."""
    sample_rate: int = 22050
    mark_freq: float = 1270.0    # Bell 103 Mark (Binary 1) in Hz
    space_freq: float = 1070.0   # Bell 103 Space (Binary 0) in Hz
    baud_rate: int = 600         # Baud rate (symbols per second)
    preamble_bits: int = 32      # Preamble carrier bits for PLL clock lock
    postamble_bits: int = 8      # Trailing silence/carrier bits
    sync_word: bytes = b"\xAA\x55" # 16-bit Frame Sync Marker
    bits_per_byte: int = 8       # Standard 8-bit data
    use_start_stop_bits: bool = True # 1 start bit (0), 8 data bits (LSB first), 1 stop bit (1)
    amplitude: float = 0.8       # Nominal peak tone amplitude


@dataclass
class GlitchProfile:
    """Degradation parameters for the 1990s Glitch Engine."""
    name: str = "medium"
    tape_hiss_amplitude: float = 0.025
    ac_hum_amplitude: float = 0.015
    ac_hum_freq: float = 60.0
    static_burst_probability: float = 0.08 # Chance per second of static burst
    burst_min_duration_ms: float = 20.0
    burst_max_duration_ms: float = 60.0
    burst_amplitude: float = 0.25
    wow_depth: float = 0.0003           # Slow tape wow
    wow_freq: float = 0.5               # Wow rate in Hz
    flutter_depth: float = 0.0002       # Rapid tape flutter
    flutter_freq: float = 6.0           # Flutter rate in Hz
    bit_depth: int = 7                  # Bit crusher quantization (1-16 bits)
    bandpass_low: float = 300.0         # POTS telephone high-pass cutoff (Hz)
    bandpass_high: float = 3400.0       # POTS telephone low-pass cutoff (Hz)
    dropout_probability: float = 0.0    # Signal dropout chance
    jitter_std_samples: float = 0.2     # Micro-timing jitter standard deviation


GLITCH_PRESETS: Dict[str, GlitchProfile] = {
    "pristine": GlitchProfile(
        name="pristine",
        tape_hiss_amplitude=0.0,
        ac_hum_amplitude=0.0,
        static_burst_probability=0.0,
        burst_amplitude=0.0,
        wow_depth=0.0,
        flutter_depth=0.0,
        bit_depth=16,
        dropout_probability=0.0,
        jitter_std_samples=0.0
    ),
    "low": GlitchProfile(
        name="low",
        tape_hiss_amplitude=0.01,
        ac_hum_amplitude=0.008,
        static_burst_probability=0.02,
        burst_amplitude=0.15,
        wow_depth=0.0001,
        flutter_depth=0.0001,
        bit_depth=8,
        dropout_probability=0.0,
        jitter_std_samples=0.1
    ),
    "medium": GlitchProfile(
        name="medium",
        tape_hiss_amplitude=0.025,
        ac_hum_amplitude=0.015,
        static_burst_probability=0.08,
        burst_amplitude=0.25,
        wow_depth=0.0003,
        flutter_depth=0.0002,
        bit_depth=7,
        dropout_probability=0.0,
        jitter_std_samples=0.2
    ),
    "high": GlitchProfile(
        name="high",
        tape_hiss_amplitude=0.05,
        ac_hum_amplitude=0.03,
        static_burst_probability=0.2,
        burst_amplitude=0.4,
        wow_depth=0.0006,
        flutter_depth=0.0004,
        bit_depth=6,
        dropout_probability=0.01,
        jitter_std_samples=0.4
    ),
    "demonic": GlitchProfile(
        name="demonic",
        tape_hiss_amplitude=0.09,
        ac_hum_amplitude=0.06,
        static_burst_probability=0.45,
        burst_amplitude=0.6,
        wow_depth=0.0012,
        flutter_depth=0.0008,
        bit_depth=5,
        dropout_probability=0.03,
        jitter_std_samples=0.8
    )
}


@dataclass
class IngestConfig:
    """Ingest agent polling settings."""
    poll_interval_sec: float = 5.0
    feed_type: str = "crypto" # "crypto", "weather", "nasa", "synthetic"
    crypto_symbols: list = field(default_factory=lambda: ["BTC", "ETH", "SOL"])
    request_timeout_sec: float = 4.0


@dataclass
class PipelineConfig:
    """Top-level pipeline configuration."""
    audio: AudioConfig = field(default_factory=AudioConfig)
    glitch: GlitchProfile = field(default_factory=lambda: GLITCH_PRESETS["medium"])
    ingest: IngestConfig = field(default_factory=IngestConfig)
    enable_audio_device: bool = False # Stream to real speaker/audio device
    tui_refresh_rate_hz: float = 30.0

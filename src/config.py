from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class AudioConfig:
    sample_rate: int = 22050
    mark_freq: float = 1270.0    # Bell 103 mark (1)
    space_freq: float = 1070.0   # Bell 103 space (0)
    baud_rate: int = 600
    preamble_bits: int = 32
    postamble_bits: int = 8
    sync_word: bytes = b"\xaa\x55"
    amplitude: float = 0.8


@dataclass
class GlitchProfile:
    name: str = "medium"
    tape_hiss_amplitude: float = 0.025
    ac_hum_amplitude: float = 0.015
    ac_hum_freq: float = 60.0
    static_burst_probability: float = 0.08
    burst_min_duration_ms: float = 20.0
    burst_max_duration_ms: float = 60.0
    burst_amplitude: float = 0.25
    wow_depth: float = 0.0003
    wow_freq: float = 0.5
    flutter_depth: float = 0.0002
    flutter_freq: float = 6.0
    bit_depth: int = 7
    bandpass_low: float = 300.0
    bandpass_high: float = 3400.0
    dropout_probability: float = 0.0
    jitter_std_samples: float = 0.2


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
        jitter_std_samples=0.0,
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
        jitter_std_samples=0.1,
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
        jitter_std_samples=0.2,
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
        jitter_std_samples=0.4,
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
        jitter_std_samples=0.8,
    ),
}


@dataclass
class IngestConfig:
    poll_interval_sec: float = 5.0
    feed_type: str = "crypto"
    crypto_symbols: List[str] = field(default_factory=lambda: ["BTC", "ETH", "SOL"])
    request_timeout_sec: float = 4.0


@dataclass
class PipelineConfig:
    audio: AudioConfig = field(default_factory=AudioConfig)
    glitch: GlitchProfile = field(default_factory=lambda: GLITCH_PRESETS["medium"])
    ingest: IngestConfig = field(default_factory=IngestConfig)
    enable_audio_device: bool = False
    enable_web: bool = True
    web_port: int = 8080
    tui_refresh_rate_hz: float = 30.0

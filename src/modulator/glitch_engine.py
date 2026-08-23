"""
The 1990s Glitch Engine.
Applies radical analog and digital degradation:
- Cassette Tape Hiss & 60Hz Ground Loop Hum
- Random Static Bursts, Pops & Crackle
- Tape Wow & Flutter (Time-domain Phase Modulation)
- Bit-Crushing (Quantization Noise & Soft Tube Saturation)
- POTS Telephone Copper Line Bandpass Filter (300Hz - 3400Hz)
- Signal Dropouts & Timing Jitter
"""

import math
import random
from typing import Tuple, Dict, Any, Optional
import numpy as np
from scipy import signal as sp_signal

from src.config import GlitchProfile, GLITCH_PRESETS


class GlitchEngine:
    """
    Simulates 1990s analog cassette tape and dial-up copper wire channel degradations.
    """

    def __init__(self, profile: Optional[GlitchProfile] = None, sample_rate: int = 22050):
        self.profile = profile or GLITCH_PRESETS["medium"]
        self.sample_rate = sample_rate

        # Precompute POTS telephone bandpass filter coefficients (300Hz to 3400Hz)
        nyq = 0.5 * self.sample_rate
        low = max(50.0, self.profile.bandpass_low) / nyq
        high = min(nyq - 100.0, self.profile.bandpass_high) / nyq
        self.bp_b, self.bp_a = sp_signal.butter(4, [low, high], btype='band')

    def set_profile(self, profile: GlitchProfile):
        """Update active glitch profile."""
        self.profile = profile
        nyq = 0.5 * self.sample_rate
        low = max(50.0, self.profile.bandpass_low) / nyq
        high = min(nyq - 100.0, self.profile.bandpass_high) / nyq
        self.bp_b, self.bp_a = sp_signal.butter(4, [low, high], btype='band')

    def apply_tape_hiss(self, audio: np.ndarray) -> np.ndarray:
        """Adds filtered analog tape hiss (Gaussian noise shaped with gentle lowpass)."""
        if self.profile.tape_hiss_amplitude <= 0:
            return audio
        noise = np.random.normal(0.0, self.profile.tape_hiss_amplitude, size=len(audio)).astype(np.float32)
        # Gentle smoothing to mimic magnetic tape grain
        kernel = np.array([0.2, 0.6, 0.2], dtype=np.float32)
        shaped_noise = np.convolve(noise, kernel, mode='same')
        return audio + shaped_noise

    def apply_ac_hum(self, audio: np.ndarray) -> np.ndarray:
        """Adds 60Hz ground loop AC hum and its second (120Hz) / third (180Hz) harmonics."""
        if self.profile.ac_hum_amplitude <= 0:
            return audio
        t = np.arange(len(audio), dtype=np.float32) / float(self.sample_rate)
        f = self.profile.ac_hum_freq
        hum = (
            np.sin(2.0 * np.pi * f * t) * 0.7 +
            np.sin(2.0 * np.pi * 2.0 * f * t) * 0.2 +
            np.sin(2.0 * np.pi * 3.0 * f * t) * 0.1
        ) * self.profile.ac_hum_amplitude
        return audio + hum.astype(np.float32)

    def apply_static_bursts(self, audio: np.ndarray) -> Tuple[np.ndarray, int]:
        """Injects sharp, random static bursts / lightning crackles and pops."""
        if self.profile.static_burst_probability <= 0:
            return audio, 0

        corrupted = audio.copy()
        duration_sec = len(audio) / float(self.sample_rate)
        expected_bursts = duration_sec * self.profile.static_burst_probability
        burst_count = np.random.poisson(expected_bursts)

        burst_events = 0
        for _ in range(burst_count):
            burst_len_ms = random.uniform(self.profile.burst_min_duration_ms, self.profile.burst_max_duration_ms)
            burst_samples = int((burst_len_ms / 1000.0) * self.sample_rate)
            if burst_samples >= len(audio):
                burst_samples = len(audio) // 2

            if burst_samples <= 0 or len(audio) <= burst_samples:
                continue

            start_idx = random.randint(0, len(audio) - burst_samples)
            # High-intensity crackle with exponential decay envelope
            t_burst = np.linspace(0, 1, burst_samples, dtype=np.float32)
            envelope = np.exp(-4.0 * t_burst)
            crackle = np.random.uniform(-1.0, 1.0, size=burst_samples).astype(np.float32) * envelope
            corrupted[start_idx : start_idx + burst_samples] += crackle * self.profile.burst_amplitude
            burst_events += 1

        return corrupted, burst_events

    def apply_wow_and_flutter(self, audio: np.ndarray) -> np.ndarray:
        """Simulates cassette motor wow (slow pitch drift) and flutter (fast mechanical wobble)."""
        if self.profile.wow_depth <= 0 and self.profile.flutter_depth <= 0:
            return audio

        n_samples = len(audio)
        t = np.arange(n_samples, dtype=np.float32) / float(self.sample_rate)

        # Time modulation delta: wow + flutter
        wow_mod = self.profile.wow_depth * np.sin(2.0 * np.pi * self.profile.wow_freq * t)
        flutter_mod = self.profile.flutter_depth * np.sin(2.0 * np.pi * self.profile.flutter_freq * t)
        total_time_shift = (wow_mod + flutter_mod) * self.sample_rate

        # Resample signal using linear interpolation with warped indices
        orig_indices = np.arange(n_samples, dtype=np.float32)
        warped_indices = orig_indices + total_time_shift
        warped_indices = np.clip(warped_indices, 0, n_samples - 1)

        return np.interp(warped_indices, orig_indices, audio).astype(np.float32)

    def apply_bit_crushing(self, audio: np.ndarray) -> np.ndarray:
        """Reduces bit depth to simulate 8-bit/6-bit 1990s ADC/DAC quantization and soft clipping."""
        if self.profile.bit_depth >= 16:
            return audio

        levels = 2 ** (self.profile.bit_depth - 1)
        quantized = np.round(audio * levels) / levels

        # Soft tube/tape saturation curve (tanh)
        saturated = np.tanh(quantized * 1.2)
        return saturated.astype(np.float32)

    def apply_telephony_bandpass(self, audio: np.ndarray) -> np.ndarray:
        """Applies 300Hz - 3400Hz POTS telephone copper line filter."""
        try:
            return sp_signal.lfilter(self.bp_b, self.bp_a, audio).astype(np.float32)
        except Exception:
            return audio

    def apply_dropouts(self, audio: np.ndarray) -> np.ndarray:
        """Simulates random analog tape dropouts and loose copper contact attenuation."""
        if self.profile.dropout_probability <= 0:
            return audio

        corrupted = audio.copy()
        duration_sec = len(audio) / float(self.sample_rate)
        expected_dropouts = duration_sec * self.profile.dropout_probability
        dropout_count = np.random.poisson(expected_dropouts)

        for _ in range(dropout_count):
            drop_len = int(random.uniform(0.01, 0.04) * self.sample_rate)
            if drop_len >= len(audio):
                continue
            start_idx = random.randint(0, len(audio) - drop_len)
            attenuation = random.uniform(0.05, 0.3)
            corrupted[start_idx : start_idx + drop_len] *= attenuation

        return corrupted

    def process(self, clean_audio: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Processes clean FSK audio through full degradation chain.
        Returns: (degraded_audio, degradation_metrics)
        """
        signal = clean_audio.copy()

        # Step 1: Tape wow & flutter (mechanical time-domain distortion)
        signal = self.apply_wow_and_flutter(signal)

        # Step 2: Signal dropouts
        signal = self.apply_dropouts(signal)

        # Step 3: POTS copper telephone bandpass
        signal = self.apply_telephony_bandpass(signal)

        # Step 4: 60Hz Ground loop hum
        signal = self.apply_ac_hum(signal)

        # Step 5: Analog tape background hiss
        signal = self.apply_tape_hiss(signal)

        # Step 6: Random static bursts / pops
        signal, burst_count = self.apply_static_bursts(signal)

        # Step 7: Bit-crushing & analog saturation
        signal = self.apply_bit_crushing(signal)

        # Normalize / prevent hard clipping overflow
        peak = np.max(np.abs(signal))
        if peak > 1.0:
            signal = signal / peak

        # Compute SNR degradation estimate
        clean_power = np.mean(clean_audio ** 2) + 1e-12
        noise_diff = signal - clean_audio
        noise_power = np.mean(noise_diff ** 2) + 1e-12
        snr_db = round(float(10.0 * np.log10(clean_power / noise_power)), 2)

        metrics = {
            "profile": self.profile.name,
            "snr_db": snr_db,
            "burst_events": burst_count,
            "bit_depth": self.profile.bit_depth,
            "peak_amplitude": round(float(np.max(np.abs(signal))), 3),
            "rms_amplitude": round(float(np.sqrt(np.mean(signal ** 2))), 3)
        }

        return signal, metrics

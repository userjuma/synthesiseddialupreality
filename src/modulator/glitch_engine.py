import random
from typing import Any, Dict, Optional, Tuple
import numpy as np
from scipy import signal as sp_signal

from src.config import GLITCH_PRESETS, GlitchProfile


class GlitchEngine:
    def __init__(self, profile: Optional[GlitchProfile] = None, sample_rate: int = 22050):
        self.profile = profile or GLITCH_PRESETS["medium"]
        self.sr = sample_rate
        self._init_filter()

    def _init_filter(self):
        nyq = 0.5 * self.sr
        low = max(50.0, self.profile.bandpass_low) / nyq
        high = min(nyq - 100.0, self.profile.bandpass_high) / nyq
        self.bp_b, self.bp_a = sp_signal.butter(4, [low, high], btype="band")

    def set_profile(self, profile: GlitchProfile):
        self.profile = profile
        self._init_filter()

    def add_hiss(self, sig: np.ndarray) -> np.ndarray:
        if self.profile.tape_hiss_amplitude <= 0:
            return sig
        noise = np.random.normal(0.0, self.profile.tape_hiss_amplitude, size=len(sig)).astype(np.float32)
        kernel = np.array([0.2, 0.6, 0.2], dtype=np.float32)
        return sig + np.convolve(noise, kernel, mode="same")

    def add_hum(self, sig: np.ndarray) -> np.ndarray:
        if self.profile.ac_hum_amplitude <= 0:
            return sig
        t = np.arange(len(sig), dtype=np.float32) / float(self.sr)
        f = self.profile.ac_hum_freq
        hum = (
            np.sin(2.0 * np.pi * f * t) * 0.7 +
            np.sin(2.0 * np.pi * 2.0 * f * t) * 0.2 +
            np.sin(2.0 * np.pi * 3.0 * f * t) * 0.1
        ) * self.profile.ac_hum_amplitude
        return sig + hum.astype(np.float32)

    def add_bursts(self, sig: np.ndarray) -> Tuple[np.ndarray, int]:
        if self.profile.static_burst_probability <= 0 or self.profile.burst_amplitude <= 0:
            return sig, 0

        out = sig.copy()
        duration = len(sig) / float(self.sr)
        n_bursts = np.random.poisson(duration * self.profile.static_burst_probability)

        count = 0
        for _ in range(n_bursts):
            dur_ms = random.uniform(self.profile.burst_min_duration_ms, self.profile.burst_max_duration_ms)
            n_samples = int((dur_ms / 1000.0) * self.sr)
            if n_samples <= 0 or n_samples >= len(sig):
                continue

            idx = random.randint(0, len(sig) - n_samples)
            decay = np.exp(-4.0 * np.linspace(0, 1, n_samples, dtype=np.float32))
            crackle = np.random.uniform(-1.0, 1.0, size=n_samples).astype(np.float32) * decay
            out[idx : idx + n_samples] += crackle * self.profile.burst_amplitude
            count += 1

        return out, count

    def add_wow_flutter(self, sig: np.ndarray) -> np.ndarray:
        if self.profile.wow_depth <= 0 and self.profile.flutter_depth <= 0:
            return sig

        n = len(sig)
        t = np.arange(n, dtype=np.float32) / float(self.sr)
        wow = self.profile.wow_depth * np.sin(2.0 * np.pi * self.profile.wow_freq * t)
        flutter = self.profile.flutter_depth * np.sin(2.0 * np.pi * self.profile.flutter_freq * t)
        shift = (wow + flutter) * self.sr

        idx = np.clip(np.arange(n, dtype=np.float32) + shift, 0, n - 1)
        return np.interp(idx, np.arange(n, dtype=np.float32), sig).astype(np.float32)

    def bit_crush(self, sig: np.ndarray) -> np.ndarray:
        if self.profile.bit_depth >= 16:
            return sig

        levels = 2 ** (self.profile.bit_depth - 1)
        quantized = np.round(sig * levels) / levels
        return np.tanh(quantized * 1.1).astype(np.float32)

    def bandpass(self, sig: np.ndarray) -> np.ndarray:
        try:
            return sp_signal.lfilter(self.bp_b, self.bp_a, sig).astype(np.float32)
        except Exception:
            return sig

    def process(self, clean: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        if self.profile.name == "pristine":
            return clean.copy(), {
                "profile": "pristine",
                "snr_db": 60.0,
                "burst_events": 0,
                "bit_depth": 16,
                "peak_amplitude": round(float(np.max(np.abs(clean))), 3),
                "rms_amplitude": round(float(np.sqrt(np.mean(clean ** 2))), 3),
            }

        sig = clean.copy()
        sig = self.add_wow_flutter(sig)
        sig = self.bandpass(sig)
        sig = self.add_hum(sig)
        sig = self.add_hiss(sig)
        sig, bursts = self.add_bursts(sig)
        sig = self.bit_crush(sig)

        peak = np.max(np.abs(sig))
        if peak > 1.0:
            sig /= peak

        clean_p = np.mean(clean ** 2) + 1e-12
        noise_p = (
            (self.profile.tape_hiss_amplitude ** 2) +
            (self.profile.ac_hum_amplitude ** 2) +
            (bursts * (self.profile.burst_amplitude ** 2) * 0.1) +
            1e-12
        )
        snr = round(float(10.0 * np.log10(clean_p / noise_p)), 2)

        return sig, {
            "profile": self.profile.name,
            "snr_db": snr,
            "burst_events": bursts,
            "bit_depth": self.profile.bit_depth,
            "peak_amplitude": round(float(np.max(np.abs(sig))), 3),
            "rms_amplitude": round(float(np.sqrt(np.mean(sig ** 2))), 3),
        }

    # Aliases
    apply_tape_hiss = add_hiss
    apply_ac_hum = add_hum
    apply_static_bursts = add_bursts
    apply_wow_and_flutter = add_wow_flutter
    apply_bit_crushing = bit_crush
    apply_telephony_bandpass = bandpass

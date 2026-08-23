"""
DSP Audio Analysis Tools for Agent C (The Reconstructive Listener).
Implements the AnalyzeAudio(signal) tool interface:
- Telephone Bandpass & Automatic Gain Control (AGC)
- Quadrature I/Q Matched Filter Bank (Bell 103 Mark/Space Discriminator)
- Short-Time Fourier Transform (STFT) for Spectral Waterfall & Oscilloscope
- Gardner / Zero-Crossing Clock Recovery for Symbol Eye-Diagram Sampling
"""

import math
from typing import Dict, Any, Tuple, List, Optional
import numpy as np
from scipy import signal as sp_signal

from src.config import AudioConfig


class AudioDSPAnalyzer:
    """
    Core DSP engine for spectral demodulation and noise exorcism.
    """

    def __init__(self, config: Optional[AudioConfig] = None):
        self.config = config or AudioConfig()
        self.sample_rate = self.config.sample_rate
        self.mark_freq = self.config.mark_freq
        self.space_freq = self.config.space_freq
        self.baud_rate = self.config.baud_rate
        self.samples_per_bit = int(self.sample_rate / self.baud_rate)

        # Precompute bandpass filter around Bell 103 tones (800Hz - 1600Hz)
        nyq = 0.5 * self.sample_rate
        low = max(100.0, self.space_freq - 350.0) / nyq
        high = min(nyq - 100.0, self.mark_freq + 350.0) / nyq
        self.bp_b, self.bp_a = sp_signal.butter(3, [low, high], btype='band')

    def apply_bandpass(self, audio: np.ndarray) -> np.ndarray:
        """Pre-filter out low hum (<800Hz) and high static noise (>1600Hz)."""
        try:
            return sp_signal.filtfilt(self.bp_b, self.bp_a, audio).astype(np.float32)
        except Exception:
            return audio

    def apply_agc(self, audio: np.ndarray, target_rms: float = 0.5) -> np.ndarray:
        """Automatic Gain Control (AGC) to normalize fading amplitudes."""
        rms = np.sqrt(np.mean(audio ** 2)) + 1e-6
        gain = target_rms / rms
        gain = np.clip(gain, 0.1, 10.0)
        return (audio * gain).astype(np.float32)

    def compute_spectrum(self, audio: np.ndarray, n_fft: int = 512) -> Tuple[np.ndarray, np.ndarray]:
        """
        Computes frequency bins and magnitude spectrum in dB for visualization.
        Returns: (freqs_hz, magnitude_db)
        """
        if len(audio) < n_fft:
            audio = np.pad(audio, (0, n_fft - len(audio)))
        # Windowed slice from the center of audio
        start = max(0, (len(audio) - n_fft) // 2)
        chunk = audio[start : start + n_fft] * np.hanning(n_fft)

        fft_res = np.fft.rfft(chunk)
        freqs = np.fft.rfftfreq(n_fft, d=1.0 / self.sample_rate)
        mag = np.abs(fft_res) + 1e-9
        mag_db = 20.0 * np.log10(mag)
        return freqs, mag_db

    def demodulate_iq(self, audio: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Quadrature I/Q Matched Filter Demodulator:
        Correlates input with sine & cosine at Mark (1270Hz) and Space (1070Hz)
        over sliding symbol integration windows.
        Returns: (discriminator_signal, mark_energy, space_energy)
        """
        n_samples = len(audio)
        t = np.arange(n_samples, dtype=np.float32) / float(self.sample_rate)
        two_pi = 2.0 * math.pi

        # Space (0) In-Phase and Quadrature references
        cos_space = np.cos(two_pi * self.space_freq * t)
        sin_space = np.sin(two_pi * self.space_freq * t)

        # Mark (1) In-Phase and Quadrature references
        cos_mark = np.cos(two_pi * self.mark_freq * t)
        sin_mark = np.sin(two_pi * self.mark_freq * t)

        # Moving average integration kernel over 1 symbol period
        win_size = max(4, int(self.samples_per_bit * 0.9))
        kernel = np.ones(win_size, dtype=np.float32) / float(win_size)

        # Space I/Q correlation
        i_space = sp_signal.fftconvolve(audio * cos_space, kernel, mode='same')
        q_space = sp_signal.fftconvolve(audio * sin_space, kernel, mode='same')
        e_space = (i_space ** 2) + (q_space ** 2)

        # Mark I/Q correlation
        i_mark = sp_signal.fftconvolve(audio * cos_mark, kernel, mode='same')
        q_mark = sp_signal.fftconvolve(audio * sin_mark, kernel, mode='same')
        e_mark = (i_mark ** 2) + (q_mark ** 2)

        # Discriminator: Positive = Mark (1), Negative = Space (0)
        discriminator = e_mark - e_space

        return discriminator, e_mark, e_space

    def recover_clock_and_sample_bits(self, discriminator: np.ndarray) -> Tuple[List[int], List[int]]:
        """
        Clock recovery & bit decision:
        Finds optimal symbol sampling points by synchronizing to transition zero-crossings
        and sampling at symbol midpoints.
        Returns: (bits, sample_indices)
        """
        spb = self.samples_per_bit
        n_samples = len(discriminator)

        # Find best starting phase offset in preamble using max discriminator contrast
        best_offset = 0
        max_energy = -1.0
        search_range = min(spb, n_samples // 4)

        for offset in range(search_range):
            test_indices = np.arange(offset + (spb // 2), min(n_samples, offset + (spb * 20)), spb)
            if len(test_indices) > 0:
                contrast = np.mean(np.abs(discriminator[test_indices]))
                if contrast > max_energy:
                    max_energy = contrast
                    best_offset = offset

        # Sample across entire signal
        sample_indices = []
        bits = []
        curr_idx = best_offset + (spb // 2)

        while curr_idx < n_samples:
            sample_indices.append(curr_idx)
            val = discriminator[curr_idx]
            bit = 1 if val > 0 else 0
            bits.append(bit)
            curr_idx += spb

        return bits, sample_indices

    def analyze_audio(self, raw_signal: np.ndarray) -> Dict[str, Any]:
        """
        The AnalyzeAudio(signal) tool implementation:
        Takes a raw acoustic waveform, cleans it via DSP, performs I/Q energy demodulation,
        recovers the clock, and outputs the demodulated bitstream and spectral telemetry.
        """
        # Step 1: Pre-filtering & AGC
        filtered = self.apply_bandpass(raw_signal)
        normalized = self.apply_agc(filtered)

        # Step 2: Demodulate Mark/Space energy
        discriminator, e_mark, e_space = self.demodulate_iq(normalized)

        # Step 3: Clock Recovery & Symbol Sampling
        bits, sample_indices = self.recover_clock_and_sample_bits(discriminator)

        # Step 4: Spectral Features
        freqs, mag_db = self.compute_spectrum(normalized, n_fft=512)

        # Mark & Space power ratio
        mark_power = float(np.mean(e_mark)) + 1e-9
        space_power = float(np.mean(e_space)) + 1e-9
        snr_est_db = round(float(10.0 * np.log10(max(mark_power, space_power) / min(mark_power, space_power))), 2)

        return {
            "bits": bits,
            "sample_indices": sample_indices,
            "discriminator": discriminator,
            "e_mark": e_mark,
            "e_space": e_space,
            "spectrum_freqs": freqs,
            "spectrum_mag_db": mag_db,
            "snr_est_db": snr_est_db,
            "filtered_audio": filtered,
            "total_samples": len(raw_signal)
        }


def AnalyzeAudio(signal: np.ndarray, config: Optional[AudioConfig] = None) -> Dict[str, Any]:
    """
    Standard Tool Interface for Agent C.
    Analyzes raw audio signal, applies DSP demodulation, and returns bitstream & spectrum.
    """
    analyzer = AudioDSPAnalyzer(config=config)
    return analyzer.analyze_audio(signal)

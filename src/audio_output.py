"""
Audio Output & Acoustic Playback Manager.
Streams 1990s acoustic waveforms to sounddevice speakers or wave files.
"""

import logging
import threading
from typing import Optional
import numpy as np

try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except Exception:
    SOUNDDEVICE_AVAILABLE = False

logger = logging.getLogger("AudioOutput")


class AudioOutputPlayer:
    """
    Manages non-blocking audio playback of acoustic signals to system speakers.
    """

    def __init__(self, sample_rate: int = 22050, enabled: bool = False):
        self.sample_rate = sample_rate
        self.enabled = enabled and SOUNDDEVICE_AVAILABLE
        self._lock = threading.Lock()

    def play_signal(self, audio: np.ndarray):
        """Play audio waveform asynchronously without blocking DSP pipeline."""
        if not self.enabled:
            return

        def _play():
            with self._lock:
                try:
                    # Clip audio to [-1.0, 1.0] and play
                    clipped = np.clip(audio, -1.0, 1.0)
                    sd.play(clipped, samplerate=self.sample_rate, blocking=False)
                except Exception as e:
                    logger.debug(f"Audio device playback error: {e}")

        threading.Thread(target=_play, daemon=True).start()

    def stop(self):
        """Stop any active audio playback."""
        if self.enabled:
            try:
                sd.stop()
            except Exception:
                pass

import logging
import threading
from typing import Optional
import numpy as np

try:
    import sounddevice as sd
    HAS_SOUNDDEVICE = True
except Exception:
    HAS_SOUNDDEVICE = False

log = logging.getLogger("AudioOutput")


class AudioOutputPlayer:
    def __init__(self, sample_rate: int = 22050, enabled: bool = False):
        self.sr = sample_rate
        self.enabled = enabled and HAS_SOUNDDEVICE
        self._lock = threading.Lock()

    def play_signal(self, sig: np.ndarray):
        if not self.enabled:
            return

        def _worker():
            with self._lock:
                try:
                    sd.play(np.clip(sig, -1.0, 1.0), samplerate=self.sr, blocking=False)
                except Exception as e:
                    log.debug(f"Audio playback error: {e}")

        threading.Thread(target=_worker, daemon=True).start()

    def stop(self):
        if self.enabled:
            try:
                sd.stop()
            except Exception:
                pass

"""
Modulator & Glitch Engine module for Agent B.
"""

from src.modulator.fsk_encoder import FSKEncoder, calculate_crc16
from src.modulator.glitch_engine import GlitchEngine
from src.modulator.modulator_agent import AcousticModulatorAgent

__all__ = [
    "FSKEncoder",
    "calculate_crc16",
    "GlitchEngine",
    "AcousticModulatorAgent"
]

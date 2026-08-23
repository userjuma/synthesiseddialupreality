# Synthesised Dial-Up Reality

Audio FSK data degradation and real-time DSP reconstruction pipeline with a terminal UI.

Encodes live JSON feeds into 1990s-era Bell 103 acoustic waveforms, degrades the signal through simulated analog channel noise (tape hiss, 60Hz hum, static bursts, wow/flutter, bit-crushing), and recovers the structured data state in real-time using spectral DSP matched filters.

## Requirements

- Python 3.10+
- `numpy`, `scipy`, `requests`, `rich`, `sounddevice`

```bash
pip install -r requirements.txt
```

## Quickstart

Run the interactive terminal interface:

```bash
python main.py
```

Run a single-pass headless benchmark:

```bash
python main.py --once --feed crypto --glitch-level medium
```

Enable real-time speaker audio playback:

```bash
python main.py --audio
```

## CLI Options

```text
usage: main.py [-h] [--feed {crypto,weather,nasa,synthetic}]
               [--glitch-level {pristine,low,medium,high,demonic}]
               [--interval INTERVAL] [--baud BAUD] [--audio] [--once] [--verbose]

options:
  --feed {crypto,weather,nasa,synthetic}
                        Data feed source (default: crypto)
  --glitch-level, -g {pristine,low,medium,high,demonic}
                        Noise profile (default: medium)
  --interval, -i INTERVAL
                        Ingest polling interval in seconds (default: 5.0)
  --baud, -b BAUD       Bell 103 baud rate (default: 600)
  --audio, -a           Enable real-time audio playback through speakers
  --once                Run a single ingest-modulate-demod cycle and exit
  --verbose, -v         Enable debug logs
```

## Architecture

1. **Ingest (`src/ingest/`)**: Polls live JSON from public endpoints (Binance ticker, Open-Meteo weather, NASA ISS telemetry, or local synthetic cyber core).
2. **Modulator & Glitch Engine (`src/modulator/`)**: 
   - Converts structured bytes into continuous-phase Bell 103 AFSK (Space: 1070 Hz, Mark: 1270 Hz) with UART framing (1 start, 8 data, 1 stop) and CRC-16-CCITT checksums.
   - Glitch engine applies analog degradation: 60Hz ground hum, tape hiss, Poisson-distributed static crackles, tape wow/flutter, and bit-depth quantization.
3. **Listener & DSP (`src/listener/`)**: 
   - Demodulates the noisy signal via quadrature I/Q matched filters and automatic gain control.
   - Recovers symbol clock, aligns to frame sync (`0xAA55`), verifies CRC, and uses heuristic field extraction if static bursts corrupt byte boundaries.
4. **Terminal UI (`src/visualizer/`)**: 
   - Renders a 3D rotating shaded torus with depth z-buffering.
   - Displays real-time ASCII voltage oscilloscope and dual-tone spectral waterfall.
   - Shows live hardware modem status LEDs (`HS`, `AA`, `CD`, `RD`, `SD`, `TR`, `MR`, `ERR`) and decoded data payload.

## Tests

Run the test suite:

```bash
python -m unittest discover tests
```

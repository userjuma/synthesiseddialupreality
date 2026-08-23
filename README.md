# Synthesised Dial-Up Reality 📟⚡

> **Radical Data Degradation & Reconstructive DSP Pipeline (1990s Dial-Up Edition)**

A high-concept, multi-stage agentic pipeline that performs radical data degradation by converting real-time, high-fidelity JSON data feeds into simulated 1990s-era acoustic interference and cassette noise, only to autonomously reconstruct the original structured data state in real-time by "listening" to the noise.

---

## 🏛️ Pipeline Architecture

```
                                  SYNTHESISED DIAL-UP REALITY
                                  
   [ Real-Time Data APIs ]
  (Crypto / Weather / NASA)
              │
              ▼
   ┌──────────────────────┐
   │       Agent A        │
   │  (The Live Ingest)   │ ─── Pulls structured JSON every 5 seconds
   └──────────────────────┘
              │  [ input_data stream ]
              ▼
   ┌──────────────────────┐
   │       Agent B        │
   │ (Acoustic Modulator  │ ─── Bell 103 / AFSK continuous-phase modulation
   │   & Glitch Engine)   │ ─── Tape Hiss + 60Hz Hum + Static Bursts + Wow/Flutter + Bit-Crushing
   └──────────────────────┘
              │  [ audio_transmission stream ]
              ▼
   ┌──────────────────────┐
   │       Agent C        │
   │ (Reconstructive DSP  │ ─── AnalyzeAudio(signal) tool interface
   │    & De-Exorcist)    │ ─── STFT + Quadrature I/Q Filter Bank + Resilient JSON Repair
   └──────────────────────┘
              │  [ decoded_data stream ]
              ▼
   ┌──────────────────────┐
   │       Agent D        │
   │ (Esoteric Terminal   │ ─── 3D Wireframe ASCII Engine (warps during static bursts)
   │     TUI Visualizer)  │ ─── Real-Time Oscilloscope + Spectral Waterfall + 1990s Modem LEDs
   └──────────────────────┘
```

---

## 🚀 Key Features

1. **Feed 1: The Live Ingest Agent (Agent A)**
   - Continuous JSON ingest loop polling every 5 seconds.
   - Built-in multi-provider support:
     - **Crypto Market Feed:** Real-time BTC, ETH, SOL tickers, 24h volume & price change.
     - **Global Weather Telemetry:** Live temperature, humidity, atmospheric pressure, and wind speed (Open-Meteo).
     - **NASA Telemetry:** Real-time International Space Station (ISS) orbital coordinates, altitude, and velocity.
     - **Synthetic Cyber Core:** Cyberpunk reactor core metrics (quantum flux, containment, warp factor).

2. **Feed 2: Acoustic Modulator & Glitch Engine (Agent B)**
   - **Bell 103 Continuous-Phase FSK (AFSK):**
     - Mark Tone (Binary 1): `1270 Hz`
     - Space Tone (Binary 0): `1070 Hz`
     - Configurable baud rate (300 / 600 / 1200 Baud).
   - **1990s Glitch Engine (Radical Analog & Digital Degradation):**
     - Magnetic cassette tape hiss & grain.
     - 60Hz / 120Hz / 180Hz ground loop AC hum.
     - Poisson-distributed static bursts and lightning crackles.
     - Cassette motor wow (slow pitch drift) and flutter (mechanical wobble).
     - Bit-crushing (4-8 bit quantization) and soft tube/tape saturation.
     - POTS copper telephone line bandpass filter (300 Hz – 3400 Hz).

3. **Feed 3: Reconstructive Listener & De-Exorcist (Agent C)**
   - **`AnalyzeAudio(signal)` Tool Interface:**
     - Pre-filtering & Automatic Gain Control (AGC).
     - Quadrature In-Phase / Quadrature-Phase (I/Q) Mark & Space matched filter bank.
     - Sliding Short-Time Fourier Transform (STFT) for spectral density.
     - Sliding Hamming correlator frame synchronizer (locks to `0xAA55` sync word).
     - CRC-16 integrity verification with autonomous **De-Exorcist** resilient JSON repair parser to salvage structured states through heavy noise bursts.

4. **Feed 4: Esoteric Visualization Terminal (Agent D / TUI)**
   - Monochrome green-on-black phosphor CRT cyberpunk aesthetic.
   - **Audio-Reactive 3D Wireframe ASCII Engine:**
     - Rotating 3D Torus / Icosahedron.
     - Vertices dynamically displace, warp, and scatter based on acoustic noise bursts and SNR drops.
     - CRT scanline flicker during static events.
   - **Live Signal Oscilloscope & Spectral Waterfall:**
     - Displays real-time acoustic waveform and Bell 103 carrier tones (`[S:1070Hz]` and `[M:1270Hz]`).
   - **1990s USRobotics / Hayes Modem Status LEDs:**
     - `[HS]` High Speed, `[AA]` Auto Answer, `[CD]` Carrier Detect, `[RD]` Receive Data, `[SD]` Send Data, `[TR]` Terminal Ready, `[MR]` Modem Ready, `[ERR]` Glitch Alert.

---

## 🛠️ Installation

```powershell
# Clone the repository
git clone https://github.com/username/synthesised-dial-up-reality.git
cd "synthesised-dial-up-reality"

# Install dependencies
pip install -r requirements.txt
```

---

## 🎮 Usage

### 1. Launch Live Interactive TUI Dashboard

```powershell
# Default: Live Crypto feed with Medium glitch degradation
python main.py

# Global Weather feed with High glitch level
python main.py --feed weather --glitch-level high

# NASA ISS telemetry with Low glitch level
python main.py --feed nasa --glitch-level low

# Enable real-time audible speaker sound output
python main.py --feed crypto --audio
```

### 2. Run Single-Pass Headless Benchmark

```powershell
python main.py --once --feed crypto --glitch-level medium
```

### 3. Command-Line Options

| Argument | Choices | Default | Description |
|---|---|---|---|
| `--feed` | `crypto`, `weather`, `nasa`, `synthetic` | `crypto` | Structured live data source |
| `--glitch-level`, `-g` | `pristine`, `low`, `medium`, `high`, `demonic` | `medium` | Glitch degradation profile |
| `--interval`, `-i` | Float (seconds) | `5.0` | Ingest polling frequency |
| `--baud`, `-b` | Integer | `600` | Bell 103 Baud rate |
| `--audio`, `-a` | Flag | `False` | Enable audible playback |
| `--once` | Flag | `False` | Single-shot headless benchmark |
| `--verbose`, `-v` | Flag | `False` | Enable debug logs |

---

## 🧪 Test Suite

Run the automated test suite covering modulator, glitch engine, DSP listener, and end-to-end integration:

```powershell
python -m unittest discover tests
```

---

## 📜 License

MIT License. Engineered for the exploration of acoustic data transmission, cybernetics, and signal processing.

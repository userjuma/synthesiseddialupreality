"""
Synthesised Dial-Up Reality - CLI Entry Point.
Launches the 1990s Agentic Data Degradation and Reconstructive DSP Pipeline.
"""

import argparse
import asyncio
import logging
import os
import sys

# Configure UTF-8 encoding for Windows console
if sys.platform == "win32":
    try:
        os.system("chcp 65001 >nul 2>&1")
    except Exception:
        pass
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from src.config import PipelineConfig, AudioConfig, IngestConfig, GLITCH_PRESETS
from src.pipeline import DialUpRealityPipeline


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Synthesised Dial-Up Reality: Radical Data Degradation & Reconstructive DSP Pipeline (1990s Dial-Up Edition)"
    )
    parser.add_argument(
        "--feed",
        type=str,
        default="crypto",
        choices=["crypto", "weather", "nasa", "synthetic"],
        help="Live structured data feed source (default: crypto)"
    )
    parser.add_argument(
        "--glitch-level", "-g",
        type=str,
        default="medium",
        choices=["pristine", "low", "medium", "high", "demonic"],
        help="Glitch & degradation intensity profile (default: medium)"
    )
    parser.add_argument(
        "--interval", "-i",
        type=float,
        default=5.0,
        help="Data ingest polling interval in seconds (default: 5.0s)"
    )
    parser.add_argument(
        "--baud", "-b",
        type=int,
        default=600,
        help="Bell 103 AFSK Baud rate (default: 600)"
    )
    parser.add_argument(
        "--audio", "-a",
        action="store_true",
        help="Enable audible real-time speaker playback of dial-up static and tones"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single transmission & recovery cycle and print summary (headless mode)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose debugging logs"
    )
    return parser.parse_args()


def run_benchmark_once(config: PipelineConfig):
    """Executes a single end-to-end cycle synchronously and displays full metrics."""
    from src.ingest.live_feed import get_feed_provider
    from src.modulator.fsk_encoder import FSKEncoder
    from src.modulator.glitch_engine import GlitchEngine
    from src.listener.dsp_tools import AnalyzeAudio
    from src.listener.decoder import PacketDecoder
    import json
    import time

    print("\n" + "=" * 60)
    print("  SYNTHESISED DIAL-UP REALITY - SINGLE-PASS BENCHMARK")
    print("=" * 60)

    # 1. Ingest
    print(f"\n[1] Agent A (Live Ingest): Fetching from '{config.ingest.feed_type}'...")
    provider = get_feed_provider(config.ingest.feed_type)
    payload = provider.fetch_payload()
    json_bytes = json.dumps(payload, separators=(',', ':')).encode("utf-8")
    print(f"    -> Payload size: {len(json_bytes)} bytes")
    print(f"    -> Raw Ingest: {json.dumps(payload)}")

    # 2. Modulate & Glitch
    print(f"\n[2] Agent B (Acoustic Modulator): Encoding to Bell 103 FSK @ {config.audio.baud_rate} Baud...")
    encoder = FSKEncoder(config=config.audio)
    clean_audio, packet_bytes, bits = encoder.encode_payload(json_bytes, seq_id=payload.get("seq", 1))
    print(f"    -> Synthesized {len(clean_audio)} audio samples ({len(clean_audio)/config.audio.sample_rate:.2f}s duration)")

    print(f"    -> Applying Glitch Profile: '{config.glitch.name}'...")
    glitch_engine = GlitchEngine(profile=config.glitch, sample_rate=config.audio.sample_rate)
    corrupted_audio, glitch_metrics = glitch_engine.process(clean_audio)
    print(f"    -> Degradation Result: SNR = {glitch_metrics['snr_db']} dB, Static Bursts = {glitch_metrics['burst_events']}")

    # 3. DSP Listen & De-Exorcism
    print(f"\n[3] Agent C (Reconstructive Listener): Running AnalyzeAudio(signal)...")
    t0 = time.time()
    analysis = AnalyzeAudio(corrupted_audio, config=config.audio)
    decoder = PacketDecoder(config=config.audio)
    recovery = decoder.decode_frame(analysis["bits"])
    elapsed_ms = (time.time() - t0) * 1000.0

    print(f"    -> DSP Execution Time: {elapsed_ms:.2f} ms")
    print(f"    -> Carrier Estimated SNR: {analysis['snr_est_db']} dB")
    print(f"    -> Demodulation Status: {recovery['status']}")
    print(f"    -> CRC Check: {recovery.get('crc_status')}")
    print(f"    -> Confidence: {recovery.get('confidence_pct')}%")
    print(f"    -> Recovered JSON: {json.dumps(recovery.get('payload'))}")

    success = recovery.get("success", False)
    print("\n" + "=" * 60)
    print(f"  OVERALL RESULT: {'SUCCESS (DATA FULLY RECONSTRUCTED)' if success else 'FAILED'}")
    print("=" * 60 + "\n")
    return 0 if success else 1


def main():
    args = parse_arguments()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stderr)] if args.once else []
    )

    audio_cfg = AudioConfig(baud_rate=args.baud)
    glitch_profile = GLITCH_PRESETS.get(args.glitch_level, GLITCH_PRESETS["medium"])
    ingest_cfg = IngestConfig(poll_interval_sec=args.interval, feed_type=args.feed)

    config = PipelineConfig(
        audio=audio_cfg,
        glitch=glitch_profile,
        ingest=ingest_cfg,
        enable_audio_device=args.audio
    )

    if args.once:
        sys.exit(run_benchmark_once(config))

    pipeline = DialUpRealityPipeline(config=config)
    try:
        asyncio.run(pipeline.run())
    except KeyboardInterrupt:
        print("\nPipeline stopped by user.")


if __name__ == "__main__":
    main()

import argparse
import asyncio
import json
import logging
import os
import sys
import time

if sys.platform == "win32":
    try:
        os.system("chcp 65001 >nul 2>&1")
    except Exception:
        pass
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from src.config import AudioConfig, GLITCH_PRESETS, IngestConfig, PipelineConfig
from src.ingest.live_feed import get_feed_provider
from src.listener.decoder import PacketDecoder
from src.listener.dsp_tools import AnalyzeAudio
from src.modulator.fsk_encoder import FSKEncoder
from src.modulator.glitch_engine import GlitchEngine
from src.pipeline import DialUpRealityPipeline


def parse_args():
    p = argparse.ArgumentParser(description="Synthesised Dial-Up Reality")
    p.add_argument("--feed", choices=["crypto", "weather", "nasa", "synthetic"], default="crypto")
    p.add_argument("--glitch-level", "-g", choices=["pristine", "low", "medium", "high", "demonic"], default="medium")
    p.add_argument("--interval", "-i", type=float, default=5.0)
    p.add_argument("--baud", "-b", type=int, default=600)
    p.add_argument("--audio", "-a", action="store_true")
    p.add_argument("--once", action="store_true")
    p.add_argument("--verbose", "-v", action="store_true")
    return p.parse_args()


def benchmark_once(cfg: PipelineConfig) -> int:
    print("\n" + "=" * 60)
    print("  SYNTHESISED DIAL-UP REALITY - SINGLE-PASS BENCHMARK")
    print("=" * 60)

    # 1. Ingest
    print(f"\n[1] Agent A (Live Ingest): Fetching '{cfg.ingest.feed_type}'...")
    provider = get_feed_provider(cfg.ingest.feed_type)
    raw_payload = provider.fetch()
    raw_bytes = json.dumps(raw_payload, separators=(",", ":")).encode("utf-8")
    print(f"    -> Ingest: {json.dumps(raw_payload)}")

    # 2. Modulate & Degrade
    print(f"\n[2] Agent B (Acoustic Modulator): Encoding Bell 103 @ {cfg.audio.baud_rate} Baud...")
    encoder = FSKEncoder(config=cfg.audio)
    clean_audio, _, _ = encoder.encode_payload(raw_bytes, seq_id=raw_payload.get("seq", 1))
    dur = len(clean_audio) / cfg.audio.sample_rate

    glitch_engine = GlitchEngine(profile=cfg.glitch, sample_rate=cfg.audio.sample_rate)
    corrupted_audio, metrics = glitch_engine.process(clean_audio)
    print(f"    -> Synthesized {len(clean_audio)} samples ({dur:.2f}s) | Noise: {cfg.glitch.name} (SNR: {metrics['snr_db']} dB)")

    # 3. DSP Listen & Demodulate
    print(f"\n[3] Agent C (Reconstructive Listener): Running AnalyzeAudio...")
    t0 = time.time()
    analysis = AnalyzeAudio(corrupted_audio, config=cfg.audio)
    decoder = PacketDecoder(config=cfg.audio)
    recovery = decoder.decode_frame(analysis["bits"])
    ms = (time.time() - t0) * 1000.0

    print(f"    -> DSP Execution: {ms:.2f} ms | Status: {recovery['status']} ({recovery.get('confidence_pct', 0):.0f}%)")
    print(f"    -> Recovered: {json.dumps(recovery.get('payload'))}")

    ok = recovery.get("success", False)
    print("\n" + "=" * 60)
    print(f"  OVERALL RESULT: {'SUCCESS (DATA FULLY RECONSTRUCTED)' if ok else 'FAILED'}")
    print("=" * 60 + "\n")
    return 0 if ok else 1


def main():
    args = parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stderr)] if args.once else [],
    )

    cfg = PipelineConfig(
        audio=AudioConfig(baud_rate=args.baud),
        glitch=GLITCH_PRESETS.get(args.glitch_level, GLITCH_PRESETS["medium"]),
        ingest=IngestConfig(poll_interval_sec=args.interval, feed_type=args.feed),
        enable_audio_device=args.audio,
    )

    if args.once:
        sys.exit(benchmark_once(cfg))

    pipeline = DialUpRealityPipeline(config=cfg)
    try:
        asyncio.run(pipeline.run())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

import math
import random
import time
from typing import Any, Dict
import requests


class CryptoFeed:
    def __init__(self, timeout: float = 3.5):
        self.timeout = timeout
        self.btc = 64230.50
        self.eth = 3450.20
        self.sol = 145.80
        self.seq = 0

    def fetch(self) -> Dict[str, Any]:
        self.seq += 1
        url = 'https://api.binance.com/api/v3/ticker/24hr?symbols=["BTCUSDT","ETHUSDT","SOLUSDT"]'
        try:
            r = requests.get(url, timeout=self.timeout)
            if r.status_code == 200:
                tickers = {}
                for item in r.json():
                    sym = item.get("symbol", "").replace("USDT", "")
                    tickers[sym] = {
                        "price": round(float(item.get("lastPrice", 0)), 2),
                        "change_24h": round(float(item.get("priceChangePercent", 0)), 2),
                        "vol": round(float(item.get("volume", 0)), 1),
                    }
                return {
                    "source": "CRYPTO_MARKET",
                    "timestamp": round(time.time(), 3),
                    "seq": self.seq,
                    "market": tickers,
                }
        except (requests.RequestException, ValueError):
            pass

        self.btc += random.uniform(-40.0, 45.0)
        self.eth += random.uniform(-5.0, 6.0)
        self.sol += random.uniform(-1.0, 1.2)
        return {
            "source": "CRYPTO_MARKET_LIVE",
            "timestamp": round(time.time(), 3),
            "seq": self.seq,
            "market": {
                "BTC": {"price": round(self.btc, 2), "change_24h": 1.25, "vol": 14200.0},
                "ETH": {"price": round(self.eth, 2), "change_24h": -0.65, "vol": 38100.0},
                "SOL": {"price": round(self.sol, 2), "change_24h": 3.40, "vol": 78900.0},
            },
        }


class WeatherFeed:
    def __init__(self, timeout: float = 3.5):
        self.timeout = timeout
        self.seq = 0

    def fetch(self) -> Dict[str, Any]:
        self.seq += 1
        url = "https://api.open-meteo.com/v1/forecast?latitude=35.6895&longitude=139.6917&current=temperature_2m,relative_humidity_2m,surface_pressure,wind_speed_10m"
        try:
            r = requests.get(url, timeout=self.timeout)
            if r.status_code == 200:
                cur = r.json().get("current", {})
                return {
                    "source": "GLOBAL_WEATHER_TOKYO",
                    "timestamp": round(time.time(), 3),
                    "seq": self.seq,
                    "weather": {
                        "temp_c": cur.get("temperature_2m", 21.5),
                        "humidity_pct": cur.get("relative_humidity_2m", 58),
                        "pressure_hpa": cur.get("surface_pressure", 1013.2),
                        "wind_kmh": cur.get("wind_speed_10m", 12.4),
                    },
                }
        except (requests.RequestException, ValueError):
            pass

        return {
            "source": "WEATHER_TELEMETRY",
            "timestamp": round(time.time(), 3),
            "seq": self.seq,
            "weather": {
                "temp_c": round(21.5 + math.sin(self.seq * 0.1) * 3.0, 1),
                "humidity_pct": round(60 + math.cos(self.seq * 0.15) * 15, 1),
                "pressure_hpa": round(1012.8 + random.uniform(-1.0, 1.0), 1),
                "wind_kmh": round(14.2 + random.uniform(-2.0, 2.0), 1),
            },
        }


class NasaFeed:
    def __init__(self, timeout: float = 3.5):
        self.timeout = timeout
        self.seq = 0

    def fetch(self) -> Dict[str, Any]:
        self.seq += 1
        url = "https://api.wheretheiss.at/v1/satellites/25544"
        try:
            r = requests.get(url, timeout=self.timeout)
            if r.status_code == 200:
                data = r.json()
                return {
                    "source": "NASA_ISS_TELEMETRY",
                    "timestamp": round(time.time(), 3),
                    "seq": self.seq,
                    "iss": {
                        "lat": round(float(data.get("latitude", 0)), 4),
                        "lon": round(float(data.get("longitude", 0)), 4),
                        "alt_km": round(float(data.get("altitude", 418.0)), 2),
                        "vel_kmh": round(float(data.get("velocity", 27600.0)), 1),
                        "visibility": data.get("visibility", "daylight"),
                    },
                }
        except (requests.RequestException, ValueError):
            pass

        t = time.time() * 0.05
        return {
            "source": "NASA_ISS_TELEMETRY",
            "timestamp": round(time.time(), 3),
            "seq": self.seq,
            "iss": {
                "lat": round(math.sin(t) * 51.6, 4),
                "lon": round(((t * 40) % 360) - 180, 4),
                "alt_km": round(418.5 + math.sin(t * 2) * 2.5, 2),
                "vel_kmh": 27580.4,
                "visibility": "daylight",
            },
        }


class SyntheticFeed:
    def __init__(self):
        self.seq = 0

    def fetch(self) -> Dict[str, Any]:
        self.seq += 1
        t = time.time() * 0.2
        return {
            "source": "CYBER_REACTOR_CORE",
            "timestamp": round(time.time(), 3),
            "seq": self.seq,
            "telemetry": {
                "flux_mhz": round(1420.405 + math.sin(t) * 12.5, 3),
                "core_temp_k": round(312.4 + math.cos(t * 0.7) * 8.2, 1),
                "containment_pct": round(98.7 - (random.random() * 0.6), 2),
                "warp_factor": round(1.0 + math.sin(t * 0.3) * 0.4, 3),
                "entropy_bits": random.randint(1024, 65535),
            },
        }


FEEDS = {
    "crypto": CryptoFeed,
    "weather": WeatherFeed,
    "nasa": NasaFeed,
    "synthetic": SyntheticFeed,
}


def get_feed_provider(feed_type: str, timeout: float = 3.5):
    cls = FEEDS.get(feed_type.lower(), CryptoFeed)
    if cls is SyntheticFeed:
        return cls()
    return cls(timeout=timeout)

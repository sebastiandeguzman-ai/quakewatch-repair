"""Practice copy of the USGS earthquake API for DSA 4153 Laboratory 5.

Use it only when the real API (https://earthquake.usgs.gov) cannot be reached.
It answers /fdsnws/event/1/query and /fdsnws/event/1/count like the real service, from the
bundled file data/usgs_ph_m5_2020_2024.csv (real events, rounded values).
The "id" and "place" fields are rebuilt here, so they differ from the real ones.

In a notebook:   import mock_usgs; mock_usgs.start()   -> then use mock_usgs.URL
In a terminal:   python mock_usgs.py
"""
import csv
import json
import math
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

PORT = 8021
URL = f"http://127.0.0.1:{PORT}"
DELAY = 0.25          # seconds per call, like a real network
HERE = Path(__file__).resolve().parent
TOWNS = [("Manila", 14.5995, 120.9842), ("Quezon City", 14.6760, 121.0437), ("Baguio", 16.4023, 120.5960),
         ("Tuguegarao", 17.6132, 121.7270), ("Legazpi", 13.1391, 123.7438), ("Puerto Princesa", 9.7392, 118.7353),
         ("Iloilo", 10.7202, 122.5621), ("Cebu City", 10.3157, 123.8854), ("Tacloban", 11.2447, 125.0048),
         ("Butuan", 8.9475, 125.5406), ("Cagayan de Oro", 8.4542, 124.6319), ("Davao", 7.1907, 125.4553),
         ("General Santos", 6.1164, 125.1716), ("Zamboanga", 6.9214, 122.0790)]
COMPASS = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]


def _place(lat, lon):
    best = None
    for name, tlat, tlon in TOWNS:
        dx = math.radians(lon - tlon) * math.cos(math.radians(tlat)) * 6371
        dy = math.radians(lat - tlat) * 6371
        d = math.hypot(dx, dy)
        if best is None or d < best[0]:
            best = (d, name, dx, dy)
    d, name, dx, dy = best
    if d > 260:
        return "Philippine Islands region" if lat < 20.5 else "Batan Islands region, Philippines"
    bearing = (math.degrees(math.atan2(dx, dy)) + 360) % 360
    return f"{d:.0f} km {COMPASS[int((bearing + 11.25) // 22.5) % 16]} of {name}, Philippines"


def _load():
    events = []
    with open(HERE / "data" / "usgs_ph_m5_2020_2024.csv", newline="") as fh:
        for i, row in enumerate(csv.DictReader(fh), start=1):
            t = datetime.strptime(row["time"], "%Y-%m-%dT%H:%MZ").replace(tzinfo=timezone.utc)
            lat, lon = float(row["latitude"]), float(row["longitude"])
            events.append({
                "type": "Feature", "id": f"ph{i:06d}",
                "properties": {"mag": float(row["mag"]), "place": _place(lat, lon),
                               "time": int(t.timestamp() * 1000), "magType": row["magType"],
                               "type": "earthquake", "status": "reviewed"},
                "geometry": {"type": "Point", "coordinates": [lon, lat, float(row["depth_km"])]}})
    return events


EVENTS = _load()


def _ms(text):
    text = text.replace("Z", "")
    t = datetime.fromisoformat(text)
    return int(t.replace(tzinfo=timezone.utc).timestamp() * 1000)


def _select(q):
    start = _ms(q["starttime"][0]) if "starttime" in q else -math.inf
    end = _ms(q["endtime"][0]) if "endtime" in q else math.inf
    minmag = float(q.get("minmagnitude", ["0"])[0])
    box = [float(q.get(k, [d])[0]) for k, d in
           [("minlatitude", -90), ("maxlatitude", 90), ("minlongitude", -180), ("maxlongitude", 180)]]
    rows = [e for e in EVENTS
            if start <= e["properties"]["time"] <= end and e["properties"]["mag"] >= minmag
            and box[0] <= e["geometry"]["coordinates"][1] <= box[1]
            and box[2] <= e["geometry"]["coordinates"][0] <= box[3]]
    if q.get("orderby", ["time"])[0] != "time-asc":
        rows = rows[::-1]
    return rows


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        try:
            rows = _select(q)
            time.sleep(DELAY)
            if u.path.endswith("/count"):
                body, code = {"count": len(rows), "maxAllowed": 20000}, 200
            elif u.path.endswith("/query"):
                offset = int(q.get("offset", ["1"])[0])
                limit = int(q.get("limit", ["20000"])[0])
                if offset < 1 or limit < 1:
                    raise ValueError("offset and limit must be 1 or more")
                page = rows[offset - 1: offset - 1 + limit]
                body, code = {"type": "FeatureCollection",
                              "metadata": {"status": 200, "count": len(page), "title": "Practice copy",
                                           "api": "practice", "limit": limit, "offset": offset},
                              "features": page}, 200
            else:
                body, code = {"error": "unknown path"}, 404
        except (ValueError, KeyError) as err:
            body, code = {"error": f"Bad Request: {err}"}, 400
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


_server = None


def start():
    """Start the practice API in the background (safe to call twice)."""
    global _server
    if _server is None:
        _server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
        threading.Thread(target=_server.serve_forever, daemon=True).start()
    return URL


if __name__ == "__main__":
    print(f"Practice USGS API on {URL}  (Ctrl+C to stop)")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()

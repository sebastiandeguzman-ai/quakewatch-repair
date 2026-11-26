"""QuakeWatch: magnitude 5+ earthquakes around the Philippines, from API to dashboard.

Four stages:
    load_new()        acquire    API   -> data/raw       (as received)
    integrate()       integrate  raw   -> data/clean     (checked, nearest city added)
    features_stage()  features   clean -> data/features  (Manila time, classes, bursts)
    report()          report     features -> figures/dashboard.png

Run everything with:  python run.py
"""
import logging
import os
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pandera.pandas as pa
import requests
from requests.adapters import HTTPAdapter, Retry

log = logging.getLogger("quakewatch")

# Practice copy of the USGS API by default. Real API: https://earthquake.usgs.gov
BASE = os.environ.get("QUAKEWATCH_BASE", "http://127.0.0.1:8021")
AREA = {"minmagnitude": 5, "minlatitude": 4, "maxlatitude": 22,
        "minlongitude": 116, "maxlongitude": 130, "orderby": "time-asc", "format": "geojson"}
FIRST_DAY, LAST_DAY = "2020-01-01", "2025-01-01"
RAW, CLEAN, FEAT, FIGS = Path("data/raw"), Path("data/clean"), Path("data/features"), Path("figures")
MAG_BINS = [4.95, 6.05, 6.95, 7.95, 10]
MAG_LABELS = ["Moderate", "Strong", "Major", "Great"]
CALLS = {"n": 0}                      # counts every API call


# ------------------------------------------------------------------ acquire
def make_session():
    session = requests.Session()
    session.headers["User-Agent"] = "DSA4153-quakewatch (student exercise)"
    retry = Retry(total=3, backoff_factor=0.5, status_forcelist=[429, 500, 503])
    session.mount("http://", HTTPAdapter(max_retries=retry))
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


def get_json(session, path, **params):
    CALLS["n"] += 1
    reply = session.get(BASE + path, params={**AREA, **params}, timeout=30)
    reply.raise_for_status()
    return reply.json()


def features_to_table(features):
    rows = [{"id": f["id"], "time": f["properties"]["time"],
             "latitude": f["geometry"]["coordinates"][1],
             "longitude": f["geometry"]["coordinates"][0],
             "depth_km": float(f["geometry"]["coordinates"][2]),
             "mag": float(f["properties"]["mag"]),
             "magType": f["properties"]["magType"],
             "place": f["properties"]["place"]} for f in features]
    table = pd.DataFrame(rows, columns=["id", "time", "latitude", "longitude",
                                        "depth_km", "mag", "magType", "place"])
    table["time"] = pd.to_datetime(table["time"], unit="ms", utc=True)
    return table


def fetch_range(start, end, limit=100, session=None):
    """Every event from start up to end, one page at a time."""
    session = session or make_session()
    pages, offset = [], 1
    while True:
        page = get_json(session, "/fdsnws/event/1/query", starttime=start, endtime=end,
                        limit=limit, offset=offset)
        table = features_to_table(page["features"])
        pages.append(table)
        if len(table) < limit:
            break
        offset += limit
    return pd.concat(pages, ignore_index=True)


def read_raw():
    table = pd.read_parquet(RAW).drop(columns="year", errors="ignore")
    return table.sort_values("time").reset_index(drop=True)


def watermark():
    """Latest time already saved in data/raw, or None."""
    if not RAW.exists() or not any(RAW.rglob("*.parquet")):
        return None
    return pd.read_parquet(RAW, columns=["time"])["time"].max()


def save_raw(table):
    stamp = str(time.time_ns())          # a new file name on every call
    for year, part in table.groupby(table["time"].dt.year):
        folder = RAW / f"year={year}"
        folder.mkdir(parents=True, exist_ok=True)
        part.to_parquet(folder / f"events_{stamp}.parquet", index=False)


def load_new(until=LAST_DAY):
    """Fetch only what is not saved yet. Returns the number of new rows."""
    fetched = fetch_range(FIRST_DAY, until)
    if len(fetched):
        save_raw(fetched)
    log.info("acquire: %d new rows", len(fetched))
    return len(fetched)


# ---------------------------------------------------------------- integrate
CONTRACT = pa.DataFrameSchema({
    "id": pa.Column(str, unique=True),
    "mag": pa.Column(float, pa.Check.between(5, 10)),
    "depth_km": pa.Column(float, pa.Check.between(0, 700)),
    "latitude": pa.Column(float, pa.Check.between(4, 22)),
    "longitude": pa.Column(float, pa.Check.between(116, 130)),
    "place": pa.Column(str),
})


def split_by_contract(raw):
    """Return (good rows, rejected rows)."""
    try:
        CONTRACT.validate(raw)
    except Exception:
        pass
    return raw, raw.iloc[0:0]


def haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance in km. Follows NumPy broadcasting."""
    p1, p2 = np.radians(lat1), np.radians(lat2)
    h = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(lon2 - lon1) / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(h))


def nearest_city(events, cities):
    """Return (city_id, distance in km) of the nearest city for every event."""
    D = haversine_km(events["longitude"].to_numpy()[:, None], events["latitude"].to_numpy()[:, None],
                     cities["latitude"].to_numpy()[None, :], cities["longitude"].to_numpy()[None, :])
    return cities["city_id"].to_numpy()[D.argmin(axis=1)], D.min(axis=1)


def integrate():
    raw = read_raw()
    good, rejects = split_by_contract(raw)
    cities = pd.read_csv("data/ref/cities.csv")
    good = good.reset_index(drop=True)
    good["city_id"], good["near_km"] = nearest_city(good, cities)
    out = good.merge(cities[["city_id", "lgu_name"]], on="city_id", validate="many_to_one")
    assert len(out) == len(good), "rows changed in the merge"
    CLEAN.mkdir(parents=True, exist_ok=True)
    out.to_parquet(CLEAN / "events.parquet", index=False)
    rejects.to_csv(CLEAN / "rejects.csv", index=False)
    log.info("integrate: %d raw, %d rejected, %d clean", len(raw), len(rejects), len(out))
    return out


# ----------------------------------------------------------------- features
def mag_class(mag):
    """Moderate 5.0-5.9, Strong 6.0-6.9, Major 7.0-7.9, Great 8.0 and above."""
    return pd.cut(mag, bins=MAG_BINS, labels=MAG_LABELS)


def depth_class(depth_km):
    return np.select([depth_km < 70, depth_km < 300], ["shallow", "intermediate"], default="deep")


def features_stage():
    t = pd.read_parquet(CLEAN / "events.parquet").sort_values("time").reset_index(drop=True)
    t["local"] = t["time"].dt.tz_localize(None).dt.tz_localize("Asia/Manila")
    t["hour_local"] = t["local"].dt.hour
    t["energy_j"] = 10 ** (1.5 * t["mag"] + 4.8)
    t["depth_class"] = depth_class(t["depth"])
    t["mag_class"] = mag_class(t["mag"])
    t["gap_h"] = t["time"].diff().dt.total_seconds() / 3600
    t["burst_id"] = (t["gap_h"] > 24).cumsum()
    FEAT.mkdir(parents=True, exist_ok=True)
    t.to_parquet(FEAT / "events.parquet", index=False)
    log.info("features: %d rows, %d Strong or above, %d bursts", len(t),
             int((t["mag_class"] >= "Strong").sum()), t["burst_id"].nunique())
    return t


# ------------------------------------------------------------------- report
def make_dashboard(f, path):
    fig, ax = plt.subplot_mosaic([["k1", "k2", "k3"], ["map", "map", "bars"]],
                                 figsize=(11, 5.5), height_ratios=[0.6, 3], layout="constrained")
    top = f.loc[f["mag"].idxmax()]
    by_city = f["lgu_name"].value_counts()
    for key, value, label in [("k1", f"{len(f)}", "Magnitude 5+ events"),
                              ("k2", f"M {top['mag']}", f"Strongest, {top['local']:%d %b %Y %H:%M} Manila time"),
                              ("k3", by_city.idxmax(), f"Most events nearby ({by_city.max()})")]:
        ax[key].axis("off")
        ax[key].text(0, 0.5, value, fontsize=20, weight="bold")
        ax[key].text(0, 0.05, label, fontsize=9, color="#555555")
    ax["map"].scatter(f["longitude"], f["latitude"], s=4 ** (f["mag"] - 4), c="#444444", alpha=0.5)
    ax["map"].set(xlabel="Longitude (°E)", ylabel="Latitude (°N)")
    counts = f["mag_class"].value_counts(sort=False)
    bars = ax["bars"].bar(counts.index.astype(str), counts.to_numpy(), color="#444444")
    ax["bars"].bar_label(bars)
    ax["bars"].set(ylabel="Events")
    fig.savefig(path, dpi=150)
    plt.close(fig)


def report():
    f = pd.read_parquet(FEAT / "events.parquet")
    FIGS.mkdir(exist_ok=True)
    make_dashboard(f, FIGS / "dashboard.png")
    log.info("report: wrote %s", FIGS / "dashboard.png")


def run_pipeline(until=LAST_DAY):
    new_rows = load_new(until)
    cleaned = integrate()
    f = features_stage()
    report()
    return {"new_rows": new_rows, "rows": len(f),
            "strong_plus": int((f["mag_class"] >= "Strong").sum()), "bursts": int(f["burst_id"].nunique())}

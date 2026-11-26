import pandas as pd
import pytest
import quakewatch as qw


def _run_features(tmp_path, monkeypatch, utc, depth_km):
    """Run features_stage() on one fake clean event; return the result row."""
    clean, feat = tmp_path / "clean", tmp_path / "features"
    clean.mkdir()
    pd.DataFrame({
        "id": ["x"], "time": pd.to_datetime([utc], utc=True),
        "latitude": [10.0], "longitude": [125.0], "depth_km": [depth_km],
        "mag": [5.5], "magType": ["mww"], "place": ["test"],
        "city_id": [1], "near_km": [1.0], "lgu_name": ["Test"],
    }).to_parquet(clean / "events.parquet", index=False)
    monkeypatch.setattr(qw, "CLEAN", clean)
    monkeypatch.setattr(qw, "FEAT", feat)
    return qw.features_stage().iloc[0]


@pytest.mark.parametrize("depth_km, expected", [
    (10.0, "shallow"), (69.9, "shallow"),
    (70.0, "intermediate"), (299.9, "intermediate"),
    (300.0, "deep"), (600.0, "deep"),
])
def test_depth_class_uses_depth_km(tmp_path, monkeypatch, depth_km, expected):   # Defect 1
    row = _run_features(tmp_path, monkeypatch, "2023-12-02T14:37:00Z", depth_km)
    assert row["depth_class"] == expected


@pytest.mark.parametrize("utc, manila", [
    ("2023-12-02T14:37:00Z", "2023-12-02 22:37"),   # the incident: 10:37 PM, not 14:37
    ("2023-12-02T20:00:00Z", "2023-12-03 04:00"),   # crosses midnight into the next day
    ("2020-01-01T00:00:00Z", "2020-01-01 08:00"),
])
def test_local_time_is_converted_to_manila(tmp_path, monkeypatch, utc, manila):   # Defect 2
    row = _run_features(tmp_path, monkeypatch, utc, 10.0)
    assert row["local"].strftime("%Y-%m-%d %H:%M") == manila
    assert row["hour_local"] == int(manila[11:13])


@pytest.mark.parametrize("depth_km, expected", [
    (0.0, "shallow"),
    (69.9, "shallow"),
    (70.0, "intermediate"),
    (299.9, "intermediate"),
    (300.0, "deep"),
    (650.0, "deep"),
])
def test_depth_class_boundaries(depth_km, expected):
    result = qw.depth_class(pd.Series([depth_km]))
    assert result[0] == expected


def test_mag_class_6_0_is_strong():
    result = qw.mag_class(pd.Series([5.9, 6.0, 6.9, 7.0]))
    assert list(result) == ["Moderate", "Strong", "Strong", "Major"]
    
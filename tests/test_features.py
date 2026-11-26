import pandas as pd
import pytest
import quakewatch as qw


@pytest.fixture
def feat(loaded):
    qw.integrate()
    return qw.features_stage()


def test_features_stage_runs(feat):
    assert len(feat) == 462
    assert {"local", "hour_local", "depth_class", "mag_class", "burst_id"} <= set(feat.columns)


def test_strongest_event_is_at_night_in_manila(feat):
    top = feat.loc[feat["mag"].idxmax()]
    assert top["local"].strftime("%Y-%m-%d %H:%M") == "2023-12-02 22:37"
    assert top["hour_local"] == 22


@pytest.mark.parametrize("mag, label", [
    (5.0, "Moderate"), (5.9, "Moderate"),
    (6.0, "Strong"), (6.9, "Strong"),
    (7.0, "Major"), (7.9, "Major"),
    (8.0, "Great"),
])
def test_mag_class_edges(mag, label):
    assert qw.mag_class(pd.Series([mag])).iloc[0] == label


def test_strong_or_above_count(feat):
    assert (feat["mag_class"] >= "Strong").sum() == 42


def test_depth_classes(feat):
    assert feat["depth_class"].value_counts().to_dict() == {"shallow": 377, "intermediate": 80, "deep": 5}

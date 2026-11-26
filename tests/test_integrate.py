import pandas as pd
import pytest
import quakewatch as qw


def test_contract_accepts_the_real_data(raw_snapshot):
    good, rejects = qw.split_by_contract(raw_snapshot)
    assert len(good) == 462
    assert len(rejects) == 0


@pytest.mark.parametrize("when, city_id", [
    ("2023-12-02 14:37", "C10"),     # the M 7.6 event east of Mindanao -> Butuan
    ("2022-07-27 00:43", "C04"),     # the M 7.0 event in northern Luzon -> Tuguegarao
    ("2021-07-23 20:49", "C01"),     # the M 6.7 event south-west of Manila -> Manila
])
def test_nearest_city_of_known_events(loaded, when, city_id):
    clean = qw.integrate()
    row = clean[clean["time"].dt.strftime("%Y-%m-%d %H:%M") == when]
    assert len(row) == 1
    assert row["city_id"].iloc[0] == city_id


def test_bad_rows_are_set_aside(loaded):
    bad = qw.read_raw().head(1).copy()
    bad["id"] = "planted-bad-row"
    bad["depth_km"] = -5.0
    qw.save_raw(bad)

    clean = qw.integrate()

    assert "planted-bad-row" not in set(clean["id"])
    assert len(clean) == 462
    rejects = pd.read_csv("data/clean/rejects.csv")
    assert list(rejects["id"]) == ["planted-bad-row"]

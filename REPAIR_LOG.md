# Repair log

Study group: ______________________   Members: Darylle Balbin, Seb, Venice, Charlize, Rhianne

## Defects

| # | Symptom (what was wrong for the user) | Cause (file, function, line; why it was wrong) | Fix (what you changed) | Test that now guards it | Fixed by |
| --- | --- | --- | --- | --- | --- |
| 1 | python run.py stops with a KeyError before the dashboard is written. | quakewatch.py, features_stage(), (line 142) passed non-existent column t["depth"] into depth_class instead of t["depth_km"]. | depth_class(t["depth"]) to depth_class(t["depth_km"]) | tests/test_group.py::test_features_stage_converts_utc_to_manila_time (plus supplied features tests) | Darylle Balbin |
| 2 | Dashboard reports the strongest earthquake at 14:37 Manila time on 2 December 2023 instead of 10:37 PM (22:37). | quakewatch.py, features_stage(), (line 139) called .dt.tz_localize(None).dt.tz_localize("Asia/Manila"), stripping UTC without shifting +8 hours. | Replaced with t["time"].dt.tz_convert("Asia/Manila") | tests/test_group.py::test_features_stage_converts_utc_to_manila_time | Darylle Balbin |
| 3 | A magnitude 6.0 earthquake is labelled Moderate instead of Strong (USGS defines 6.0 to 6.9 as Strong). | quakewatch.py, MAG_BINS (line 33); the upper cutoff for Moderate was set to 6.05 instead of 5.95, putting 6.0 in the (4.95, 6.05] bin. | Changed MAG_BINS = [4.95, 6.05, 6.95, 7.95, 10] to MAG_BINS = [4.95, 5.95, 6.95, 7.95, 10] | tests/test_group.py::test_mag_class_6_0_is_strong (plus supplied mag_class tests) | Seb |
| 4 | | | | | |
| 5 | | | | | |
| 6 | | | | | |

## Our own tests (in `tests/test_group.py`)

| Test name | Tool used (`parametrize`, fake API, `caplog`) | What it proves | Fails on the broken code? | Written by |
| --- | --- | --- | --- | --- |
| tests_group.py | @pytest.mark.parametrize | features_stage() runs cleanly using depth_km and converts UTC timestamps accurately to Asia/Manila (+08:00) across day boundaries. | Yes | Darylle Balbin |
| test_mag_class_6_0_is_strong | unit test | Verifies mag_class() classifies 5.9 as Moderate, 6.0 and 6.9 as Strong, and 7.0 as Major. | Yes | Seb |
| | | | | |

## Logging we added

| Where (function) | Level | Message | Why this level |
| --- | --- | --- | --- |
| | | | |
| | | | |
| | | | |

## One thing we learned about debugging

(two or three sentences)
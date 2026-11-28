# Repair log

Study group: ______________________   Members: ______________________________________________

## Defects

| # | Symptom (what was wrong for the user) | Cause (file, function, line; why it was wrong) | Fix (what you changed) | Test that now guards it | Fixed by |
| --- | --- | --- | --- | --- | --- |
| 1 | python run.py stops with a KeyError before the dashboard is written. | quakewatch.py, features_stage(), (line 142) passed non-existent column t["depth"] into depth_class instead of t["depth_km"]. | depth_class(t["depth"]) to depth_class(t["depth_km"]) | tests/test_group.py::test_features_stage_converts_utc_to_manila_time (plus supplied features tests) | Darylle Balbin |
| 2 | Dashboard reports the strongest earthquake at 14:37 Manila time on 2 December 2023 instead of 10:37 PM (22:37). | quakewatch.py, features_stage(), (line 139) called .dt.tz_localize(None).dt.tz_localize("Asia/Manila"), stripping UTC without shifting +8 hours. | Replaced with t["time"].dt.tz_convert("Asia/Manila") | tests/test_group.py::test_features_stage_converts_utc_to_manila_time | Darylle Balbin |
| 3 | A magnitude 6.0 earthquake is labelled Moderate instead of Strong (USGS defines 6.0 to 6.9 as Strong). | quakewatch.py, MAG_BINS (line 33); the upper cutoff for Moderate was set to 6.05 instead of 5.95, putting 6.0 in the (4.95, 6.05] bin. | Changed MAG_BINS = [4.95, 6.05, 6.95, 7.95, 10] to MAG_BINS = [4.95, 5.95, 6.95, 7.95, 10] | tests/test_group.py::test_mag_class_6_0_is_strong (plus supplied mag_class tests) | Seb |
| 4 | Earthquakes east of Mindanao are listed under a city in northern Luzon, more than 1,000 km away. | quakewatch.py, nearest_city() (line 142); passed events["longitude"] as lat1 and events["latitude"] as lon1 into haversine_km(lat1, lon1, lat2, lon2), swapping event coordinates and skewing all computed distances. | Swapped the first two arguments to haversine_km(events["latitude"].to_numpy()[:, None], events["longitude"].to_numpy()[:, None], ...). | tests/test_integrate.py::test_nearest_city_of_known_events and tests/test_group.py::test_nearest_city_uses_lat_lon_order | Your Name |
| 5 | Running the pipeline twice put every earthquake in data/raw two times; new_rows was 462 on the second run instead of 0.	quakewatch.py, load_new(): it always called fetch_range(FIRST_DAY, until), ignoring watermark(), and save_raw() writes a new file each call, so the whole history was appended again.	load_new() now starts at the watermark (or FIRST_DAY when data/raw is empty). Because the API starttime is inclusive, it also drops fetched rows whose id is already in data/raw, and applies drop_duplicates(subset="id") before saving.	tests/test_acquire.py::test_second_load_adds_nothing, test_ids_stay_unique_after_two_loads, tests/test_pipeline.py::test_run_twice_gives_the_same_numbers, tests/test_group.py::test_resumed_load_has_no_duplicates
| 6 | Bad rows were never rejected: rejects.csv was always empty and rows that broke the data contract (for example mag = 3.0) ended up in data/clean. | quakewatch.py, split_by_contract() (line ___): wrapped CONTRACT.validate(raw) in try/except Exception: pass, so every validation error was silently swallowed, then always returned raw as good and an empty frame as rejected. | Validate with lazy=True and catch SchemaErrors. Use err.failure_cases["index"] to find the bad rows, return them as rejects, return the remaining rows as good, and log a WARNING with the rejected count. | tests/test_group.py::test_split_by_contract_rejects_bad_rows | Rhianne |

## Our own tests (in `tests/test_group.py`)

| Test name | Tool used (`parametrize`, fake API, `caplog`) | What it proves | Fails on the broken code? | Written by |
| --- | --- | --- | --- | --- |
| tests_group.py | @pytest.mark.parametrize | features_stage() runs cleanly using depth_km and converts UTC timestamps accurately to Asia/Manila (+08:00) across day boundaries. | Yes | Darylle Balbin |
| test_rejected_rows_emit_warning | caplog | integrate() emits a WARNING on logger "quakewatch" when invalid rows (e.g., depth_km = -5.0) are rejected by the data contract. | Yes | Your Name |
| test_split_by_contract_rejects_bad_rows | direct call with a small DataFrame | split_by_contract() puts a valid row (mag = 5.5) in good and a row that breaks the contract (mag = 3.0) in rejects, instead of passing everything through. | Yes | Rhianne |
| | | | | |

## Logging we added

| Where (function) | Level | Message | Why this level |
| --- | --- | --- | --- |
| | | | |
| | | | |
| | | | |

## One thing we learned about debugging

A bare `except: pass` hides failures: the pipeline looked healthy and printed normal numbers while it was quietly accepting bad data. Errors should be logged or handled, never silently swallowed. Every check also needs a test that proves it can actually fail, because a check that can never fail protects nothing.
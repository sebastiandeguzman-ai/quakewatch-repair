# QuakeWatch Repair Shop (DSA 4153, Week 15 group activity)

This is a copy of the QuakeWatch pipeline with **six planted defects**. Your group repairs it until every test passes.
It runs on a practice copy of the USGS earthquake API on your own laptop, so you do not need the internet.

## Set up (once)

    pip install pytest responses pandas numpy pyarrow pandera requests matplotlib

## Files

| File | What it is |
| --- | --- |
| `quakewatch.py` | The pipeline: acquire, integrate, features, report. **This is the file you repair.** |
| `run.py` | Runs the whole pipeline once |
| `mock_usgs.py` | Practice copy of the USGS API (do not change) |
| `data/` | The events the practice API serves, and `data/ref/cities.csv` |
| `tests/` | The supplied tests and `conftest.py` (do not change) |
| `INCIDENTS.md` | The six problem reports |
| `REPAIR_LOG.md` | Your record of every repair |

## Work

    python -m pytest -q            # all tests, short output
    python -m pytest -x            # stop at the first failure
    python -m pytest -k mag_class  # only tests whose name contains "mag_class"
    python -m pytest --lf          # only the tests that failed last time
    python -m pytest --pdb -x      # open the debugger where the first test fails
    python run.py                  # the whole pipeline

To start the data again from nothing, delete `data/raw`, `data/clean`, `data/features` and `figures`.

## Done means

1. `python -m pytest -q` shows every supplied test passing.
2. `tests/test_group.py` holds at least three tests of your own: one with `parametrize`, one that fakes the API
   (`responses` or `monkeypatch`), one with `caplog`.
3. `quakewatch.py` logs a WARNING when rows are rejected, uses `log.exception` where it catches an error,
   and `run.py` also writes the log to `logs/run.log`.
4. `python run.py` twice in a row prints the same numbers, with `new_rows` equal to 0 the second time.
5. `REPAIR_LOG.md` is complete.

## Submit (one ZIP per group)

`quakewatch.py`, `run.py`, the `tests/` folder, `REPAIR_LOG.md`, `pytest_output.txt` (from
`python -m pytest -v > pytest_output.txt`), `logs/run.log`, and `disclosure.txt` (members, who did what,
and any help used, including AI tools).

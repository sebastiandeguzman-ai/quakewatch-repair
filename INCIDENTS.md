# QuakeWatch incident reports

Six problems were reported after the last change to `quakewatch.py`. Each report describes what a user saw.
It does not say where the cause is. Some problems only show up after you fix another one.

| # | Report |
| --- | --- |
| 1 | "`python run.py` stops with a `KeyError` before the dashboard is written." |
| 2 | "The dashboard says the strongest earthquake struck at 14:37 Manila time on 2 December 2023. The news reported it at 10:37 PM." |
| 3 | "A magnitude 6.0 earthquake is labelled *Moderate*. The USGS calls 6.0 to 6.9 *Strong*." |
| 4 | "Earthquakes east of Mindanao are listed under a city in northern Luzon, more than 1,000 km away." |
| 5 | "I ran the pipeline twice. Now every earthquake is in the data two times." |
| 6 | "We added a test row with a depth of -5 km to `data/raw`. The log says 0 rejected, and the row is in the clean file." |

## Rules

1. Start with `python -m pytest -q`. Read the failures before you open `quakewatch.py`.
2. Fix one incident at a time. Run the tests after every change.
3. Do not edit the supplied tests or `tests/conftest.py`. Add your own tests in a new file, `tests/test_group.py`.
4. Write every repair in `REPAIR_LOG.md`.

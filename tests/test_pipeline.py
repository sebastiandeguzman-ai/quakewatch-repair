from pathlib import Path

import quakewatch as qw


def test_run_twice_gives_the_same_numbers(project):
    first = qw.run_pipeline()
    second = qw.run_pipeline()
    assert first["new_rows"] == 462
    assert second["new_rows"] == 0
    assert {k: v for k, v in first.items() if k != "new_rows"} == \
           {k: v for k, v in second.items() if k != "new_rows"}
    assert Path("figures/dashboard.png").stat().st_size > 10_000

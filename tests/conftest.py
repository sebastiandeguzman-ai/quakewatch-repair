"""Shared set-up for the tests. You do not need to change this file."""
import shutil
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import mock_usgs
import quakewatch as qw


@pytest.fixture(scope="session", autouse=True)
def practice_api():
    """Start the practice copy of the USGS API once for the whole test run."""
    mock_usgs.DELAY = 0
    qw.BASE = mock_usgs.start()


@pytest.fixture
def project(tmp_path, monkeypatch):
    """An empty project folder with only data/ref inside. Every test gets a fresh one."""
    shutil.copytree(ROOT / "data" / "ref", tmp_path / "data" / "ref")
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture(scope="session")
def raw_snapshot(tmp_path_factory, practice_api):
    """All events fetched once, as one table, for tests that do not need the API."""
    return qw.fetch_range(qw.FIRST_DAY, qw.LAST_DAY)


@pytest.fixture
def loaded(project, raw_snapshot):
    """A project folder whose data/raw already holds every event."""
    qw.save_raw(raw_snapshot)
    return project

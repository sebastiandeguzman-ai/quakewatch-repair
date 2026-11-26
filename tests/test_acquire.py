import pandas as pd
import quakewatch as qw


def test_first_load_gets_every_event(project):
    assert qw.load_new() == 462
    assert len(qw.read_raw()) == 462


def test_second_load_adds_nothing(project):
    qw.load_new()
    assert qw.load_new() == 0


def test_ids_stay_unique_after_two_loads(project):
    qw.load_new()
    qw.load_new()
    raw = qw.read_raw()
    assert raw["id"].is_unique
    assert len(raw) == 462

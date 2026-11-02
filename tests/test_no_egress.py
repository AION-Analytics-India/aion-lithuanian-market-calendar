"""Nothing reaches the network unless a refresh was asked for."""
from __future__ import annotations

import importlib
import socket
from datetime import date

import pytest


@pytest.fixture
def tripwire(monkeypatch):
    attempts: list = []

    def refuse(address, *args, **kwargs):
        attempts.append(address)
        raise AssertionError(f"unexpected network egress to {address!r}")

    class NoSocket(socket.socket):
        def connect(self, address, *args, **kwargs):
            refuse(address)

        def connect_ex(self, address, *args, **kwargs):
            refuse(address)

    monkeypatch.setattr(socket, "socket", NoSocket)
    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.setenv("AION_LT_CALENDAR_OFFLINE", "1")
    return attempts


def test_importing_the_package_opens_no_connection(tripwire):
    import aion_lithuanian_market_calendar

    importlib.reload(aion_lithuanian_market_calendar)
    assert tripwire == []


def test_ordinary_questions_open_no_connection(tripwire):
    from aion_lithuanian_market_calendar import is_daylight_saving, is_market_open, session_bounds_utc

    is_market_open("2026-02-16")
    is_daylight_saving(date(2026, 7, 1))
    session_bounds_utc(date(2026, 7, 1))
    assert tripwire == []

import importlib.util
from pathlib import Path

import pytest

_spec = importlib.util.spec_from_file_location("docker_cleanup", Path(__file__).with_name("docker_cleanup.py"))
dc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dc)


@pytest.fixture(autouse=True)
def cache(tmp_path, monkeypatch):
    monkeypatch.setattr(dc, "CACHE", tmp_path)


@pytest.mark.parametrize(
    "command",
    [
        "docker run -d --name x img",
        "docker run --rm img prog",
        "docker compose up -d db",
        "docker compose -f a.yaml -p proj up -d",
        "docker compose run --rm migrate",
        "docker-compose up -d",
        "docker create img",
        "docker container run img",
    ],
)
def test_can_create(command):
    assert dc.can_create(command)


@pytest.mark.parametrize(
    "command",
    ["docker ps -a", "docker compose down", "docker rm -f x", "docker stop x", "docker images", "docker compose -p x ps"],
)
def test_not_create(command):
    assert not dc.can_create(command)


def test_pre_post_attributes_only_new_containers(monkeypatch):
    seen = [{"a", "b"}, {"a", "b", "c"}]
    monkeypatch.setattr(dc, "all_ids", lambda: seen.pop(0))
    payload = {"session_id": "s1", "tool_use_id": "t1", "tool_input": {"command": "docker compose up -d"}}
    dc.pre(payload)
    dc.post(payload)
    assert dc.load("s1")["owned"] == ["c"]


def test_non_creating_command_records_nothing(monkeypatch):
    monkeypatch.setattr(dc, "all_ids", lambda: {"a"})
    payload = {"session_id": "s1", "tool_use_id": "t1", "tool_input": {"command": "docker ps"}}
    dc.pre(payload)
    dc.post(payload)
    assert dc.load("s1")["owned"] == []


def test_stop_blocks_once_with_commands(monkeypatch):
    dc.save("s1", {"pre": {}, "owned": ["c"]})
    monkeypatch.setattr(
        dc, "survivors",
        lambda owned: [
            {"id": "c", "name": "p-db-1", "status": "Exited (0) 1 hour ago", "project": "p"},
            {"id": "d", "name": "tei", "status": "Up", "project": ""},
        ],
    )
    result = dc.stop({"session_id": "s1"})
    assert result["decision"] == "block"
    assert "docker compose -p p down" in result["reason"]
    assert "docker rm -f tei" in result["reason"]
    assert "-v" in result["reason"] and "volumes stay" in result["reason"]
    assert dc.stop({"session_id": "s1", "stop_hook_active": True}) is None


def test_stop_silent_when_nothing_left(monkeypatch):
    dc.save("s1", {"pre": {}, "owned": ["c"]})
    monkeypatch.setattr(dc, "survivors", lambda owned: [])
    assert dc.stop({"session_id": "s1"}) is None
    assert dc.stop({"session_id": "other"}) is None


def test_docker_unavailable_fails_open(monkeypatch):
    monkeypatch.setattr(dc, "_docker", lambda args: None)
    assert dc.all_ids() is None
    assert dc.survivors(["c"]) == []

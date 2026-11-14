import pytest

import ram_guard

GUARD = "python ~/claude-config/scripts/gpu_run.py run --resource ram --wait -- "


@pytest.mark.parametrize("command", [
    "pytest",
    "uv run pytest",
    "uv run --frozen pytest -q",
    "python -m pytest -q",
    "python -m pytest tests/",
    "cd hooks; python -m pytest -q 2>&1 | Select-Object -Last 2",
    "pnpm test",
    "pnpm build:web",
    "npm run build",
    "next build",
    "docker build -t x .",
    "docker buildx build .",
    "docker compose build api",
    "docker-compose build",
])
def test_refuses_heavy_commands(command):
    assert ram_guard.refusal(command)


@pytest.mark.parametrize("command", [
    "python -m pytest -q test_ram_guard.py",
    "uv run pytest tests/test_api.py::test_health",
    "uv run ruff check .",
    "uv run mypy",
    "pnpm lint:web",
    "git log --oneline",
    "docker compose up -d",
    "echo build",
    GUARD + "uv run pytest",
    GUARD + "pnpm build:web",
    "python ~/claude-config/scripts/gpu_run.py run --resource=ram --wait -- docker build .",
])
def test_allows_light_or_guarded_commands(command):
    assert ram_guard.refusal(command) == ""


def test_gpu_only_lock_is_not_enough():
    assert ram_guard.refusal("python gpu_run.py run --wait -- uv run pytest")


def test_message_gives_wrapped_command():
    msg = ram_guard.refusal("uv run pytest")
    assert "--resource ram --wait -- uv run pytest" in msg

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
    "docker compose ps",
    "docker compose down",
    "echo build",
    "git pull --rebase; echo up",
    GUARD + "uv run pytest",
    GUARD + "pnpm build:web",
    "python ~/claude-config/scripts/gpu_run.py run --resource=ram --wait -- docker build .",
    "python ~/claude-config/scripts/gpu_run.py hold --resource ram --wait -- docker compose up -d",
    "python ~/claude-config/scripts/gpu_run.py hold --wait --purpose x -- docker compose -f a.yml up -d api",
    "python gpu_run.py hold --resource ram -- docker-compose up --detach",
    GUARD + "docker compose up --abort-on-container-exit",  # foreground: ends with the command
])
def test_allows_light_or_guarded_commands(command):
    assert ram_guard.refusal(command) == ""


def test_a_gpu_run_now_covers_ram_too():
    # since 2026-11-17 a GPU `run` takes the RAM lock first
    assert ram_guard.refusal("python gpu_run.py run --wait -- uv run pytest") == ""


@pytest.mark.parametrize("command", [
    "docker compose up -d",
    "docker compose -p real285 -f compose.yaml -f compose.reranker.yaml up -d",
    "docker-compose up -d db",
    "docker compose up --wait",
    "cd app && docker compose up -d --build",
    "docker compose up",  # foreground, but unguarded
    GUARD + "docker compose up -d",  # `run` releases at once while the stack keeps running
])
def test_refuses_an_unheld_compose_stack(command):
    msg = ram_guard.refusal(command)
    assert "Compose stack" in msg and "gpu_run.py hold --resource ram" in msg


def test_stack_message_gives_the_wrapped_command():
    msg = ram_guard.refusal(GUARD + "docker compose up -d")
    assert "-- docker compose up -d`" in msg


def test_message_gives_wrapped_command():
    msg = ram_guard.refusal("uv run pytest")
    assert "--resource ram --wait -- uv run pytest" in msg

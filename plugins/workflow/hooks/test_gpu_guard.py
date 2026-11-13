import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

_spec = importlib.util.spec_from_file_location("gpu_guard", Path(__file__).with_name("gpu_guard.py"))
assert _spec and _spec.loader
gpu_guard = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gpu_guard)

GPU_COMPOSE = """services:
  reranker:
    image: ghcr.io/huggingface/text-embeddings-inference:turing-1.9.4
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
"""
CPU_COMPOSE = "services:\n  db:\n    image: postgres:17\n"


@pytest.fixture
def proj(tmp_path):
    (tmp_path / "gpu").mkdir()
    (tmp_path / "gpu" / "compose.yaml").write_text(CPU_COMPOSE)
    (tmp_path / "gpu" / "compose.reranker.yaml").write_text(GPU_COMPOSE)
    (tmp_path / "cpu").mkdir()
    (tmp_path / "cpu" / "compose.yaml").write_text(CPU_COMPOSE)
    (tmp_path / "gpudefault").mkdir()
    (tmp_path / "gpudefault" / "docker-compose.yml").write_text(GPU_COMPOSE)
    return tmp_path


@pytest.mark.parametrize(
    "command",
    [
        "docker run --rm --gpus all ghcr.io/huggingface/text-embeddings-inference:turing-1.9.4 --model-id x",
        "docker run -d --gpus=all --name rr image",
        "docker container run --gpus all --name rr image",
        "docker.exe run --gpus all -l gpu-guard.task=t1 image",
        "cd gpu && docker compose -f compose.yaml -f compose.reranker.yaml up -d",
        "docker compose --file gpu/compose.reranker.yaml up -d reranker",
        "cd gpudefault; docker compose up -d",
        "docker-compose -f gpu/compose.reranker.yaml up",
    ],
)
def test_unguarded_gpu_start_is_refused(command, proj):
    assert "outside the machine-wide GPU lock" in gpu_guard.refusal(command, str(proj))


@pytest.mark.parametrize(
    "command",
    [
        "python ~/claude-config/scripts/gpu_run.py hold --wait --purpose t -- docker run -d --gpus all --name rr image",
        "python \"C:/Users/x/claude-config/scripts/gpu_run.py\" hold -- docker compose -f gpu/compose.reranker.yaml up -d",
        "docker run --rm image",
        "docker ps --filter label=gpu-guard.task",
        "docker compose -f gpu/compose.reranker.yaml down",
        "docker compose -f gpu/compose.reranker.yaml logs reranker",
        "cd cpu && docker compose up -d",
        "docker compose -f missing.yaml up -d",
        "grep -n 'docker run --gpus' notes.md",
        "",
    ],
)
def test_allowed(command, proj):
    assert gpu_guard.refusal(command, str(proj)) == ""


def test_guarded_but_unnamed_docker_run_is_refused(proj):
    cmd = "python gpu_run.py hold -- docker run -d --rm --gpus all image"
    assert "unnamed GPU container" in gpu_guard.refusal(cmd, str(proj))


def test_hook_output_denies_and_ignores_other_tools(proj):
    script = str(Path(__file__).with_name("gpu_guard.py"))

    def call(payload):
        return subprocess.run([sys.executable, script], input=json.dumps(payload), capture_output=True,
                              text=True).stdout

    out = call({"tool_name": "Bash", "cwd": str(proj), "tool_input": {"command": "docker run --gpus all x"}})
    assert json.loads(out)["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert call({"tool_name": "Read", "tool_input": {"command": "docker run --gpus all x"}}) == ""
    assert call({"tool_name": "Bash", "tool_input": {"command": "ls"}}) == ""


@pytest.mark.parametrize(
    "command",
    [
        "timeout 280 docker run --rm --gpus all --name t img",
        "timeout 60 docker run --rm postgres:17",
        "timeout -k 5 60 docker container run --rm img",
        "gtimeout 60 docker run img",
        "timeout 600 docker compose -f gpu/compose.yaml up",
        "timeout 600 docker compose -p x run --rm api pytest",
        "timeout 600 docker-compose up",
        "timeout 300 python gpu_run.py run -- docker run --gpus all --name t img",
    ],
)
def test_timeout_around_foreground_container_is_refused(command, proj):
    assert "time limit on the docker client" in gpu_guard.refusal(command, str(proj))


@pytest.mark.parametrize(
    "command",
    [
        "timeout 60 docker ps",
        "timeout 60 docker run -d --name t postgres:17",
        "timeout 120 docker compose up -d",
        "timeout 120 docker compose up --wait",
        "timeout 60 docker logs t",
        "timeout 30 docker stop t",
        "timeout 60 curl -s localhost:8080/health",
    ],
)
def test_timeout_without_foreground_container_is_allowed(command, proj):
    assert gpu_guard.refusal(command, str(proj)) == ""


# --- gaps closed 2026-11-13: program options after the image, `docker start`, CPU-only compose services ---

MIXED_COMPOSE = """services:
  db:
    image: postgres:17
  api:
    image: api
    depends_on: [reranker]
  web:
    image: web
    depends_on:
      db:
        condition: service_started
  reranker:
    image: tei
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              capabilities: [gpu]
"""


@pytest.fixture
def mixed(tmp_path):
    (tmp_path / "compose.yaml").write_text(MIXED_COMPOSE)
    return tmp_path


@pytest.mark.parametrize(
    "command",
    [
        "timeout 60 docker run --rm img prog -d",
        "timeout 60 docker run --rm --name t img sh -c 'x' --detach",
        "timeout 60 docker run -e A=1 -v d:/d img prog -d",
        "timeout 60 docker compose run --rm api prog -d",
    ],
)
def test_program_dash_d_after_the_image_is_not_detached(command, proj):
    assert "time limit on the docker client" in gpu_guard.refusal(command, str(proj))


@pytest.mark.parametrize(
    "command",
    [
        "timeout 60 docker run -d img",
        "timeout 60 docker run --rm -itd --name t img",
        "timeout 60 docker run --detach -e A=1 img prog",
        "timeout 60 docker run -p 80:80 -d img",
        "timeout 60 docker compose run -d api",
    ],
)
def test_dash_d_before_the_image_is_detached(command, proj):
    assert gpu_guard.refusal(command, str(proj)) == ""


def test_run_option_values_are_not_taken_for_the_image():
    opts, idx = gpu_guard._run_split(["--rm", "--gpus", "all", "-e", "A=1", "--name", "t", "img", "prog", "--gpus", "x"])
    assert idx == 7
    assert ("--gpus", "all") in opts and ("--name", "t") in opts


def test_gpu_run_option_after_the_image_is_not_a_gpu_request(proj):
    assert gpu_guard.refusal("docker run --name t img prog --gpus all", str(proj)) == ""
    assert "outside the machine-wide GPU lock" in gpu_guard.refusal("docker run --rm --name t --gpus all img", str(proj))


def test_docker_start_of_a_gpu_container_is_refused(proj, monkeypatch):
    monkeypatch.setattr(gpu_guard, "_container_requests_gpu", lambda names: names == ["rr"])
    assert "outside the machine-wide GPU lock" in gpu_guard.refusal("docker start rr", str(proj))
    assert "outside the machine-wide GPU lock" in gpu_guard.refusal("docker container start -a rr", str(proj))
    assert "outside the machine-wide GPU lock" in gpu_guard.refusal("docker restart -t 5 rr", str(proj))
    assert gpu_guard.refusal("docker start db", str(proj)) == ""
    guarded = "python gpu_run.py hold --wait -- docker start rr"
    assert gpu_guard.refusal(guarded, str(proj)) == ""


def test_container_requests_gpu_reads_docker_inspect(monkeypatch):
    def fake(out):
        return lambda *a, **k: subprocess.CompletedProcess(a, 0, stdout=out, stderr="")

    monkeypatch.setattr(gpu_guard.subprocess, "run", fake('[{"Driver":"nvidia","Capabilities":[["gpu"]]}] runc\n'))
    assert gpu_guard._container_requests_gpu(["rr"])
    monkeypatch.setattr(gpu_guard.subprocess, "run", fake("null runc\n"))
    assert not gpu_guard._container_requests_gpu(["db"])
    monkeypatch.setattr(gpu_guard.subprocess, "run", fake("null nvidia\n"))
    assert gpu_guard._container_requests_gpu(["old"])

    def boom(*a, **k):
        raise OSError("no docker")

    monkeypatch.setattr(gpu_guard.subprocess, "run", boom)
    assert not gpu_guard._container_requests_gpu(["rr"])  # fails open
    assert not gpu_guard._container_requests_gpu([])


@pytest.mark.parametrize(
    "command",
    [
        "docker compose up -d db",
        "docker compose up -d web",
        "docker compose up -d --no-deps db",
        "docker compose up --scale db=2 -d db",
    ],
)
def test_compose_up_of_cpu_only_service_is_allowed_beside_a_gpu_service(command, mixed):
    assert gpu_guard.refusal(command, str(mixed)) == ""


@pytest.mark.parametrize(
    "command",
    [
        "docker compose up -d",
        "docker compose up -d reranker",
        "docker compose up -d api",  # depends_on pulls the GPU service in
        "docker compose up -d db api",
    ],
)
def test_compose_up_that_starts_a_gpu_service_is_refused(command, mixed):
    assert "outside the machine-wide GPU lock" in gpu_guard.refusal(command, str(mixed))


def test_compose_files_are_merged_for_gpu_detection(proj):
    cmd = "docker compose -f gpu/compose.yaml -f gpu/compose.reranker.yaml up -d db"
    assert gpu_guard.refusal(cmd, str(proj)) == ""  # db is CPU-only in both files
    assert "outside" in gpu_guard.refusal(cmd.replace("up -d db", "up -d reranker"), str(proj))


def test_unparsable_compose_falls_back_to_the_whole_file(tmp_path, monkeypatch):
    (tmp_path / "compose.yaml").write_text("services: [unclosed\n  deploy: capabilities: [gpu]\n")
    assert "outside" in gpu_guard.refusal("docker compose up -d db", str(tmp_path))

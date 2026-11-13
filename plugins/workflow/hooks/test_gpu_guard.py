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

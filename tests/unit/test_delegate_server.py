import json

import anyio
import pytest
from mcp import Client
from omg_delegate.server import server
from support import guardrails


@pytest.fixture
def configured(tmp_path, monkeypatch):
    config = tmp_path / "guardrails.json"
    config.write_text(json.dumps(guardrails.build(tmp_path / "docker.sock")))
    monkeypatch.setenv("OMG_DELEGATE_CONFIG", str(config))
    monkeypatch.setenv("OMG_DELEGATE_STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    return tmp_path


def call(arguments):
    async def run():
        async with Client(server) as client:
            return await client.call_tool("delegate", arguments)

    return anyio.run(run)


def payload(result):
    return result.structured_content


def test_the_tool_hands_its_arguments_to_the_harness(configured):
    result = call(
        {
            "task": "summarise",
            "volumes": [{"host_path": "relative/path", "mode": "rw"}],
            "backend": "ollama",
            "model": "qwen3.8:27b-mlx",
        }
    )
    assert not result.is_error
    assert payload(result)["status"] == "refused"
    assert payload(result)["reason"] == "forbidden_volume"


def test_optional_arguments_are_passed_only_when_given(configured):
    result = call(
        {
            "task": "summarise",
            "volumes": [{"host_path": "/", "mode": "ro"}],
            "backend": "ollama",
            "model": "qwen3.8:27b-mlx",
            "timeout_seconds": 999999,
        }
    )
    assert payload(result)["reason"] == "invalid_argument"
    assert "ceiling" in payload(result)["message"]


def test_the_schema_rejects_a_backend_outside_the_enum(configured):
    result = call(
        {
            "task": "summarise",
            "volumes": [{"host_path": "/", "mode": "ro"}],
            "backend": "vllm",
            "model": "qwen3.8:27b-mlx",
        }
    )
    assert result.is_error


def test_every_call_leaves_an_audit_line(configured):
    call(
        {
            "task": "secret task text",
            "volumes": [{"host_path": "relative", "mode": "rw"}],
            "backend": "ollama",
            "model": "qwen3.8:27b-mlx",
        }
    )
    audit = (configured / "state" / "audit.jsonl").read_text()
    assert '"outcome": "refused"' in audit
    assert "secret task text" not in audit

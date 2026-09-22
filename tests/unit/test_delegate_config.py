import json
from pathlib import Path

import pytest
from omg_delegate.config import Config

REAL = Path(__file__).resolve().parents[2] / "configs" / "delegate" / "guardrails.json"
HOME = Path("/synthetic/home")


@pytest.fixture
def config():
    return Config.from_dict(json.loads(REAL.read_text()), home=HOME)


def test_the_image_is_pinned_by_digest(config):
    assert "@sha256:" in config.image


def test_home_placeholders_are_expanded(config):
    assert HOME / ".ssh" in config.forbidden_paths
    assert not any("$HOME" in str(p) for p in config.forbidden_paths)


def test_credential_directories_and_the_runtime_socket_are_forbidden(config):
    names = {p.name for p in config.forbidden_paths}
    assert {".ssh", ".aws", ".gnupg", ".docker", "docker.sock"} <= names


def test_hosts_that_inject_stored_credentials_are_forbidden(config):
    assert {"api.openai.com", "github.com", "*.anthropic.com"} <= set(
        config.forbidden_hosts
    )


def test_the_registry_lists_the_supported_pairs(config):
    pairs = set(config.pairs())
    assert ("ollama", "qwen3.8:27b-mlx") in pairs
    assert ("ollama", "gemma4:12b") in pairs
    assert ("llama-server", "gpt-oss:20b") in pairs
    assert ("exo", "gpt-oss:120b") in pairs
    assert ("llama-server", "gpt-oss:120b") not in pairs


def test_exo_is_experimental_and_the_others_are_not(config):
    assert config.backends["exo"].experimental
    assert not config.backends["ollama"].experimental


def test_every_backend_has_an_endpoint_the_sandbox_can_reach(config):
    for backend in config.backends.values():
        assert backend.endpoint.startswith("host.docker.internal:")


def test_the_timeout_ceiling_is_above_the_default(config):
    assert 0 < config.timeout_default <= config.timeout_max


def test_the_agent_command_is_not_overridden_by_default(config):
    assert config.agent_command is None


def test_the_agent_command_can_be_overridden_by_the_configuration_only():
    data = json.loads(REAL.read_text())
    data["agent_command"] = ["sh", "-c", "echo probe"]
    assert Config.from_dict(data, home=HOME).agent_command == ("sh", "-c", "echo probe")

import pytest
from omg_delegate.config import Config
from omg_delegate.models import Policy
from omg_delegate.network import forbidden_allow, rules
from support import guardrails


@pytest.fixture
def config(tmp_path):
    return Config.from_dict(
        guardrails.build(tmp_path / "docker.sock"), home=tmp_path / "home"
    )


@pytest.mark.parametrize(
    "host",
    [
        "**",
        "*",
        "api.openai.com:443",
        "auth.openai.com:443",
        "*.anthropic.com:443",
        "github.com:443",
        "raw.githubusercontent.com:443",
        "localhost:22",
        "127.0.0.1:80",
        "host.docker.internal:5432",
    ],
)
def test_allow_that_widens_the_boundary_is_forbidden(config, host):
    assert forbidden_allow(host, config, "ollama")


@pytest.mark.parametrize(
    "host", ["pypi.org:443", "registry.npmjs.org:443", "example.org"]
)
def test_allow_of_an_ordinary_host_is_permitted(config, host):
    assert forbidden_allow(host, config, "ollama") is None


def test_the_backend_endpoint_is_the_only_local_port_that_may_be_allowed(config):
    assert forbidden_allow("host.docker.internal:11434", config, "ollama") is None
    assert forbidden_allow("localhost:11434", config, "ollama") is None
    assert forbidden_allow("host.docker.internal:11434", config, "llama-server")
    assert forbidden_allow("localhost:11434", config, "llama-server")


def test_the_backend_endpoint_comes_first_and_nothing_else_is_allowed_by_default(
    config,
):
    result = rules([], "ollama", kit_hosts=[], config=config)
    assert result.allow == ["host.docker.internal:11434", "localhost:11434"]
    assert result.deny == []


def test_requested_allows_and_denies_are_applied(config):
    policies = [Policy("allow", "pypi.org:443"), Policy("deny", "example.com:443")]
    result = rules(policies, "ollama", kit_hosts=[], config=config)
    assert result.allow == [
        "host.docker.internal:11434",
        "localhost:11434",
        "pypi.org:443",
    ]
    assert result.deny == ["example.com:443"]


def test_kit_default_hosts_are_masked(config):
    kit = ["api.openai.com:443", "registry.npmjs.org:443"]
    result = rules([], "ollama", kit_hosts=kit, config=config)
    assert result.deny == kit


def test_a_kit_host_the_caller_allowed_is_not_masked(config):
    kit = ["api.openai.com:443", "registry.npmjs.org:443"]
    policies = [Policy("allow", "registry.npmjs.org:443")]
    result = rules(policies, "ollama", kit_hosts=kit, config=config)
    assert result.deny == ["api.openai.com:443"]


def test_a_caller_deny_of_a_kit_host_is_not_listed_twice(config):
    kit = ["registry.npmjs.org:443"]
    policies = [Policy("deny", "registry.npmjs.org:443")]
    result = rules(policies, "ollama", kit_hosts=kit, config=config)
    assert result.deny == ["registry.npmjs.org:443"]

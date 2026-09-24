from omg_delegate.models import Volume
from omg_delegate.render import agent_config

ENDPOINT = "host.docker.internal:11434"


def render(volumes, commands=(), backend="ollama", model="qwen3.8:27b-mlx"):
    return agent_config(backend, model, ENDPOINT, volumes, list(commands))


def test_the_model_and_endpoint_come_from_the_backend():
    config = render(
        [Volume("/w/space", "rw")], backend="llama-server", model="gpt-oss-20b"
    )
    assert config["model"] == "llama-server/gpt-oss-20b"
    options = config["provider"]["llama-server"]["options"]
    assert options["baseURL"] == f"http://{ENDPOINT}/v1"
    assert "gpt-oss-20b" in config["provider"]["llama-server"]["models"]


def test_edits_are_denied_except_inside_read_write_volumes():
    edit = render([Volume("/w/space", "rw"), Volume("/w/docs", "ro")])["permission"][
        "edit"
    ]
    assert edit["*"] == "deny"
    allowed = [pattern for pattern, verdict in edit.items() if verdict == "allow"]
    assert allowed and all("w/space" in pattern for pattern in allowed)
    assert not any("w/docs" in pattern for pattern in allowed)


def test_edit_patterns_cover_the_path_with_and_without_the_leading_slash():
    edit = render([Volume("/w/space", "rw")])["permission"]["edit"]
    assert "/w/space/*" in edit and "w/space/*" in edit


def test_shell_commands_are_denied_by_default():
    assert render([Volume("/w/space", "rw")])["permission"]["bash"] == {"*": "deny"}


def test_only_the_listed_shell_commands_are_allowed():
    bash = render([Volume("/w/space", "rw")], commands=["pytest -q"])["permission"][
        "bash"
    ]
    assert bash == {"*": "deny", "pytest -q": "allow"}


def test_web_fetch_is_denied():
    assert render([Volume("/w/space", "rw")])["permission"]["webfetch"] == "deny"


def test_every_volume_may_be_read_from_outside_the_working_directory():
    external = render([Volume("/w/space", "rw"), Volume("/w/docs", "ro")])[
        "permission"
    ]["external_directory"]
    assert external["*"] == "deny"
    assert external["/w/docs/*"] == "allow" and external["/w/space/*"] == "allow"


def test_a_clone_workspace_is_writable_but_read_only_volumes_stay_read_only():
    volumes = [Volume("/w/repo", "clone"), Volume("/w/docs", "ro")]
    edit = render(volumes)["permission"]["edit"]
    assert edit["*"] == "allow"
    assert edit["/w/docs/*"] == "deny" and edit["w/docs/*"] == "deny"

"""A synthetic guardrail configuration for tests. Nothing here is read from the real plugin configuration."""

ENDPOINTS = {
    "ollama": "host.docker.internal:11434",
    "llama-server": "host.docker.internal:8080",
    "exo": "host.docker.internal:52415",
}
PAIRS = {
    "qwen3.8:27b-mlx": ["ollama"],
    "gemma4:12b": ["ollama"],
    "gpt-oss:20b": ["ollama", "llama-server"],
    "gpt-oss:120b": ["exo"],
}
FORBIDDEN_HOSTS = [
    "api.openai.com",
    "*.openai.com",
    "chatgpt.com",
    "api.anthropic.com",
    "*.anthropic.com",
    "claude.ai",
    "api.github.com",
    "github.com",
    "*.githubusercontent.com",
]


def build(
    socket,
    probe_urls=None,
    image="sandbox-image@sha256:feedface",
    cpus=2,
    memory_mib=2048,
    canary_host="example.com:443",
):
    probe_urls = probe_urls or {}
    return {
        "image": image,
        "limits": {
            "cpus": cpus,
            "memory_mib": memory_mib,
            "timeout_seconds": {"default": 3, "maximum": 600},
        },
        "forbidden_paths": ["$HOME/.ssh", "$HOME/.aws", str(socket)],
        "forbidden_hosts": FORBIDDEN_HOSTS,
        "canary_host": canary_host,
        "backends": {
            name: {
                "endpoint": endpoint,
                "probe_url": probe_urls.get(name, "http://127.0.0.1:9/v1/models"),
                "experimental": name == "exo",
            }
            for name, endpoint in ENDPOINTS.items()
        },
        "models": {
            model: {b: model for b in backends} for model, backends in PAIRS.items()
        },
    }

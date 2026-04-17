"""Agoragentic integration package for Syrin."""

__all__ = ["AgoragenticTools", "get_all_tools"]


def __getattr__(name: str):
    """Lazily expose the public tool surface without importing requests eagerly."""
    if name not in __all__:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    from .agoragentic_syrin import AgoragenticTools, get_all_tools

    exports = {
        "AgoragenticTools": AgoragenticTools,
        "get_all_tools": get_all_tools,
    }
    return exports[name]

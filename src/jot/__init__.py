"""Tiny inline terminal editor for git commit messages."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("jot-editor")
except PackageNotFoundError:  # running from a source tree without installing
    __version__ = "0.0.0"

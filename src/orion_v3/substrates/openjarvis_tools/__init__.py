"""ORION extensions implemented as OpenJarvis-native tools.

This package must not become a second execution framework. Custom tools belong
here only when the pinned OpenJarvis substrate does not already provide the
required capability.
"""

from .filesystem_search import OrionFilesystemSearchTool

__all__ = ["OrionFilesystemSearchTool"]

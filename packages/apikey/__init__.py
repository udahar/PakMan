"""apikey — API key management and rotation for PakMan-aware applications."""

__version__ = "0.1.0"

from .key_manager import KeyManager, KeyScope, KeyRotationPolicy, APIKey

__all__ = [
    "KeyManager",
    "KeyScope",
    "KeyRotationPolicy",
    "APIKey",
]

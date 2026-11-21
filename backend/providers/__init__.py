"""Provider manager: choose the AI backend by name.

HAMO_PROVIDER = gemini (default) | openai (experimental) | mock (offline demo)
Every provider module exposes:  generate(system, turns) -> str
"""

import os

from .base import ProviderError, load_env

__all__ = ["ProviderError", "active_provider_name", "get_provider"]


def active_provider_name():
    load_env()
    return (os.getenv("HAMO_PROVIDER") or "gemini").strip().lower()


def get_provider(name=None):
    name = (name or active_provider_name()).strip().lower()
    if name == "gemini":
        from . import gemini_provider as module
    elif name == "openai":
        from . import openai_provider as module
    elif name == "mock":
        from . import mock_provider as module
    else:
        raise ProviderError("مزوّد الذكاء الاصطناعي المحدد في ملف .env غير معروف.", 503,
                            f"unknown HAMO_PROVIDER={name!r}")
    return module

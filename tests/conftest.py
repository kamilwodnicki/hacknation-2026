"""Tests never call a paid LLM API: the provider is forced off before settings are read.
LLM behaviour is tested with a fake client (tests/test_llm.py)."""

import os

os.environ["LLM_PROVIDER"] = "none"

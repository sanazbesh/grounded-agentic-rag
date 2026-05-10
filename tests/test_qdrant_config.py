from __future__ import annotations

from agentic_rag.indexing import DEFAULT_COLLECTION_NAME, qdrant_config_from_env


def test_qdrant_config_from_env_defaults_to_dense_collection() -> None:
    config = qdrant_config_from_env({})

    assert config.url == ""
    assert config.collection_name == DEFAULT_COLLECTION_NAME
    assert config.enabled is False


def test_qdrant_config_from_env_reads_qdrant_env_vars() -> None:
    config = qdrant_config_from_env(
        {
            "QDRANT_URL": " http://qdrant:6333 ",
            "QDRANT_COLLECTION_NAME": " legal_chunks ",
        }
    )

    assert config.url == "http://qdrant:6333"
    assert config.collection_name == "legal_chunks"
    assert config.enabled is True


def test_qdrant_config_from_env_uses_default_for_blank_collection_override() -> None:
    config = qdrant_config_from_env({"QDRANT_COLLECTION_NAME": "  "})

    assert config.collection_name == DEFAULT_COLLECTION_NAME

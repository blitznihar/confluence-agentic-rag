from __future__ import annotations

from weaviate.classes.config import DataType, Property


def ensure_schema(client) -> None:
    """Create ConfluenceChunk collection if it doesn't exist."""
    existing = client.collections.list_all()
    if "ConfluenceChunk" in existing:
        return

    client.collections.create(
        name="ConfluenceChunk",
        properties=[
            Property(name="page_id", data_type=DataType.TEXT),
            Property(name="title", data_type=DataType.TEXT),
            Property(name="url", data_type=DataType.TEXT),
            Property(name="chunk", data_type=DataType.TEXT),
            Property(name="space_key", data_type=DataType.TEXT),
            Property(name="version", data_type=DataType.INT),
        ],
        vectorizer_config=None,  # we provide vectors ourselves
    )

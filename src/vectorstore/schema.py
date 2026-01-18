from __future__ import annotations


def ensure_schema(client) -> None:
    """
    Creates ConfluenceChunk collection if it doesn't exist.
    Uses Weaviate v4 client config classes (data_type not dataType).
    """
    from weaviate.classes.config import Property, DataType, Configure

    # list existing collections
    existing = set(client.collections.list_all().keys())
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
        # We supply vectors ourselves (sentence-transformers), so disable internal vectorizer:
        vectorizer_config=Configure.Vectorizer.none(),
    )

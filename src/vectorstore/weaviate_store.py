from __future__ import annotations

from typing import Any, Dict, List, Optional
import weaviate
from weaviate.connect import ConnectionParams


class WeaviateStore:
    def __init__(self, url: str = "http://localhost:6060", grpc_port: int = 6061):
        self.http_url = url.rstrip("/")
        self.grpc_port = grpc_port

        self.client = weaviate.WeaviateClient(
            connection_params=ConnectionParams.from_url(
                self.http_url,
                grpc_port=self.grpc_port
            )
        )
        self.client.connect()

    def close(self) -> None:
        self.client.close()

    def upsert_chunks(self, chunks: List[Dict[str, Any]]) -> None:
        """
        chunks items must have:
        - properties: dict
        - vector: list[float]
        """
        col = self.client.collections.get("ConfluenceChunk")
        with col.batch.dynamic() as batch:
            for item in chunks:
                batch.add_object(properties=item["properties"],
                                 vector=item["vector"])

    def semantic_search(
        self,
        query_vector: List[float],
        top_k: int = 8,
        where_filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        col = self.client.collections.get("ConfluenceChunk")

        # v4 filter: build from where_filter if provided (keep simple for now)
        # Example filter support: space_key equals
        filters = None
        if where_filter and "space_key" in where_filter:
            from weaviate.classes.query import Filter
            filters = Filter.by_property("space_key").equal(
                where_filter["space_key"]
                )

        resp = col.query.near_vector(
            near_vector=query_vector,
            limit=top_k,
            filters=filters,
            return_metadata=["distance"],
        )

        out = []
        for obj in resp.objects:
            props = obj.properties
            out.append({
                "page_id": props.get("page_id"),
                "title": props.get("title"),
                "url": props.get("url"),
                "chunk": props.get("chunk"),
                "space_key": props.get("space_key"),
                "version": props.get("version"),
                "distance": obj.metadata.distance,
            })
        return out

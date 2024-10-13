from qdrant_client import QdrantClient
from qdrant_client.http import models as rest


def delete_document_from_qdrant(
    client: QdrantClient, collection_name: str, document_id: str
):
    search_result = client.scroll(
        collection_name=collection_name,
        scroll_filter=rest.Filter(
            must=[
                rest.FieldCondition(
                    key="metadata.document_id", match=rest.MatchValue(value=document_id)
                )
            ]
        ),
        limit=10000,
    )

    points_to_delete = [point.id for point in search_result[0]]

    if not points_to_delete:
        print(f"No vectors found for document: {document_id}")
        return

    delete_result = client.delete(
        collection_name=collection_name,
        points_selector=rest.PointIdsList(points=points_to_delete),
    )

    print(f"Deleted {len(points_to_delete)} vectors for document: {document_id}")
    print(f"Delete operation status: {delete_result.status}")

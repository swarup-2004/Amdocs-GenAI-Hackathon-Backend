from qdrant_client import QdrantClient, models
from dotenv import load_dotenv
import os
import uuid
load_dotenv()

QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL")


qdrant_client = QdrantClient(
    url=QDRANT_URL, 
    api_key=QDRANT_API_KEY,
)


def insert_point(collection_name: str, data: dict) -> str:
    # Create collection
    id = str(uuid.uuid4())
    payload ={
        'id': id,
        'data': data
    }

    qdrant_client.upsert(
        collection_name=collection_name,
        points=[
            models.PointStruct(
                id=id,
                payload=payload,
                vector=[0.0] * 100,
            ),
        ],
    )
    return id

def search_point(collection_name: str, id: str) -> dict:
    result = qdrant_client.retrieve(
        collection_name=collection_name, 
        ids=[id]
    )

    return result[0].payload
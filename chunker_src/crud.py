import chromadb


async def delete_all_records_in_collection(
    chroma_host: str,
    chroma_port: int,
    collection_name: str,
) -> None:
    """
    Delete all records in the specified ChromaDB collection using the async client.

    Args:
        chroma_host (str): ChromaDB host.
        chroma_port (int): ChromaDB port.
        collection_name (str): Name of the collection to delete all records from.

    Raises:
        Exception: If connection, collection retrieval, or deletion fails.
    """
    client = await chromadb.AsyncHttpClient(host=chroma_host, port=chroma_port)
    collection = await client.get_collection(collection_name)
    # Fetch all ids in the collection
    results = await collection.get()
    ids = results.get("ids", [])
    if ids:
        await collection.delete(ids=ids)

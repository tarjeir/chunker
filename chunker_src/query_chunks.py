import logging
from chunker_src import model as chunker_model
import chromadb

async def query_chunks_core(
    query_text: str,
    config: chunker_model.ChunkAndVectoriseConfig,
    logger: logging.Logger,
) -> chunker_model.QueryResult:
    """
    Query chunks from a ChromaDB collection and return their texts and file paths.

    Args:
        query_text (str): The text to query for.
        config (chunker_model.ChunkAndVectoriseConfig): Configuration object.
        logger (logging.Logger): Logger instance.

    Returns:
        chunker_model.QueryResult: The result containing chunk texts and file paths.
    """
    try:
        client = await chromadb.AsyncHttpClient(
            host=config.chroma_host,
            port=config.chroma_port,
        )
        collection = await client.get_or_create_collection(config.collection_name)
    except Exception as e:
        logger.error(f"Failed to connect to ChromaDB or get collection: {e}")
        raise

    try:
        results = await collection.query(
            query_texts=[query_text],
            n_results=10,
            include=["documents", "metadatas"],
        )
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise

    chunks = []
    paths = []
    if results and "documents" in results and "metadatas" in results:
        for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
            chunks.append(doc)
            paths.append(meta.get("path", ""))

    return chunker_model.QueryResult(chunks=chunks, paths=paths)

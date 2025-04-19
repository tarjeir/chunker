import logging
from chunker_src import model as chunker_model
import chromadb


async def query_chunks_core(
    query_text: str,
    config: chunker_model.QueryChunksConfig,
    logger: logging.Logger,
    n_results: int = 10,
) -> list[chunker_model.QueryResult]:
    """
    Query chunks from a ChromaDB collection and return a list of QueryResult objects.

    Each QueryResult contains a single chunk and its associated file path.

    Args:
        query_text (str): The text to query for.
        config (chunker_model.ChunkAndVectoriseConfig): Configuration object.
        logger (logging.Logger): Logger instance.
        n_results (int): Number of results to return from the query (default: 10).

    Returns:
        list[chunker_model.QueryResult]: List of QueryResult objects, each with one chunk and one path.
    """
    if n_results < 1:
        logger.warning("n_results < 1; setting n_results to 1.")
        n_results = 1

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
            n_results=n_results,
            include=["documents", "metadatas"],
        )
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise

    query_results = []
    documents = results.get("documents")
    metadatas = results.get("metadatas")
    if (
        documents
        and isinstance(documents, list)
        and len(documents) > 0
        and isinstance(documents[0], list)
        and metadatas
        and isinstance(metadatas, list)
        and len(metadatas) > 0
        and isinstance(metadatas[0], list)
    ):
        for doc, meta in zip(documents[0], metadatas[0]):
            chunk = [doc]
            path: list[str] = [
                str(meta.get("path", "")) if isinstance(meta, dict) else ""
            ]
            query_results.append(chunker_model.QueryResult(chunks=chunk, path=path))
    else:
        logger.warning(
            "QueryResult missing or malformed: no documents or metadatas found."
        )

    return query_results

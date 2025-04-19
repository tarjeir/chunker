from dataclasses import dataclass


@dataclass
class ChunkAndVectoriseConfig:
    """
    Configuration for chunking and vectorising source files.

    Args:
        chroma_host (str): Hostname for the ChromaDB server.
        chroma_port (int): Port for the ChromaDB server.
        collection_name (str): Name of the ChromaDB collection.
        max_batch_size (int): Maximum batch size for collection.add().
        language (str): Programming language for chunking.
    """

    chroma_host: str
    chroma_port: int
    collection_name: str
    max_batch_size: int
    language: str


@dataclass
class QueryChunksConfig:
    """
    Configuration for querying chunks from a ChromaDB collection.

    Args:
        chroma_host (str): Hostname for the ChromaDB server.
        chroma_port (int): Port for the ChromaDB server.
        collection_name (str): Name of the ChromaDB collection.
        n_results (int): Number of results to return from the query.
    """

    chroma_host: str
    chroma_port: int
    collection_name: str
    n_results: int = 10


@dataclass
class QueryResult:
    """
    Result of a chunk query.

    Args:
        chunks (list[str]): The retrieved chunk texts.
        paths (list[str]): The file paths corresponding to each chunk.
    """

    chunks: list[str]
    path: list[str]

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
    chroma_host: str = "localhost"
    chroma_port: int = 8000
    collection_name: str = "default"
    max_batch_size: int = 64
    language: str = "python"

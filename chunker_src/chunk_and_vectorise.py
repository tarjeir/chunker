import asyncio
import logging
import os
import uuid
from pathlib import Path
from chromadb.api.models.AsyncCollection import AsyncCollection
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language
import chromadb
from typing import Union
from chunker_src import model as chunker_model

PathLike = Union[str, Path]


def _get_uuid() -> str:
    return uuid.uuid4().hex


async def _expand_and_validate_path(path: PathLike, absolute: bool = False) -> str:
    """
    Expand and validate the file path.

    Args:
        file_path (str): Path to the file.

    Returns:
        str: Absolute expanded file path.
    """
    expanded = os.path.expanduser(os.path.expandvars(path))
    if absolute:
        return os.path.abspath(expanded)

    return str(expanded)


async def _remove_existing_chunks(
    collection, collection_lock, full_path_str: str
) -> int:
    """
    Remove existing chunks for the file from the collection.

    Args:
        collection: The ChromaDB collection object.
        collection_lock: Asyncio lock for collection operations.
        full_path_str (str): Absolute file path.

    Returns:
        int: Number of existing chunks removed.
    """
    async with collection_lock:
        existing = await collection.get(
            where={"path": full_path_str},
            include=["metadatas"],
        )
        num_existing_chunks = len(existing["ids"]) if "ids" in existing else 0

        if num_existing_chunks:
            await collection.delete(where={"path": full_path_str})

    return num_existing_chunks


async def _read_and_chunk_file(
    full_path_str: str, semaphore: asyncio.Semaphore, language: str, logger
) -> list[str]:
    """
    Read the file and split it into chunks.

    Args:
        full_path_str (str): Absolute file path.
        semaphore (asyncio.Semaphore): Semaphore to limit concurrency.
        language (str): Programming language for chunking.
        logger: Logger instance.

    Returns:
        list[str]: List of text chunks.
    """
    try:
        async with semaphore:
            with open(full_path_str, "r", encoding="utf-8") as f:
                code = f.read()
            splitter = RecursiveCharacterTextSplitter.from_language(
                getattr(Language, language.upper())
            )
            chunks = splitter.split_text(code)
            return chunks
    except UnicodeDecodeError:
        logger.warning(
            f"UnicodeDecodeError: Skipping file {full_path_str} (probably binary)"
        )
        return []
    except Exception as e:
        logger.warning(f"Error reading or chunking file {full_path_str}: {e}")
        return []


def _compute_chunk_metadata(chunks: list[str], full_path_str: str) -> list[dict]:
    """
    Compute line ranges for each chunk.

    Args:
        chunks (list[str]): List of text chunks.
        full_path_str (str): Absolute file path.

    Returns:
        list[dict]: List of metadata dicts for each chunk.
    """
    metas = []
    current_line = 0
    for chunk in chunks:
        chunk_lines = chunk.count("\n") + 1
        start_line = current_line
        end_line = current_line + chunk_lines - 1
        metas.append({"path": full_path_str, "start": start_line, "end": end_line})
        current_line = end_line + 1
    return metas


async def _add_chunks_to_collection(
    collection,
    collection_lock,
    chunks: list[str],
    metas: list[dict],
    max_batch_size: int,
):
    """
    Add chunks and metadata to the collection in batches.

    Args:
        collection: The ChromaDB collection object.
        collection_lock: Asyncio lock for collection operations.
        chunks (list[str]): List of text chunks.
        metas (list[dict]): List of metadata dicts.
        max_batch_size (int): Maximum batch size for collection.add().
        full_path_str (str): Absolute file path.

    Returns:
        None
    """
    async with collection_lock:
        for idx in range(0, len(chunks), max_batch_size):
            inserted_chunks = chunks[idx : idx + max_batch_size]
            await collection.add(
                ids=[_get_uuid() for _ in inserted_chunks],
                documents=inserted_chunks,
                metadatas=metas[idx : idx + max_batch_size],
            )


async def _update_stats(stats: dict[str, int], stats_lock, key: str):
    """
    Update the stats dictionary.

    Args:
        stats (dict[str, int]): Stats dictionary.
        stats_lock: Asyncio lock for stats.
        key (str): 'add' or 'update'.

    Returns:
        None
    """
    async with stats_lock:
        stats[key] += 1


async def add_file_with_langchain(
    file_path: str,
    logger: logging.Logger,
    collection: AsyncCollection,
    collection_lock: asyncio.Lock,
    stats: dict[str, int],
    stats_lock: asyncio.Lock,
    max_batch_size: int,
    semaphore: asyncio.Semaphore,
    language: str = "python",
) -> None:
    """
    Add a file's contents to a ChromaDB collection, chunked and with metadata.

    Args:
        file_path (str): Path to the file to process.
        logger (logging.Logger): Logger instance.
        collection (object): The ChromaDB collection object.
        collection_lock (asyncio.Lock): Asyncio lock for collection operations.
        stats (dict[str, int]): Dictionary to track add/update stats.
        stats_lock (asyncio.Lock): Asyncio lock for stats.
        max_batch_size (int): Maximum batch size for collection.add().
        semaphore (asyncio.Semaphore): Semaphore to limit concurrency.
        language (str): Programming language for chunking.

    Returns:
        None
    """
    full_path_str = await _expand_and_validate_path(file_path)
    logger.info(f"Processing file: {full_path_str}")

    num_existing_chunks = await _remove_existing_chunks(
        collection, collection_lock, full_path_str
    )

    chunks = await _read_and_chunk_file(full_path_str, semaphore, language, logger)
    if not chunks or (len(chunks) == 1 and chunks[0] == ""):
        return

    metas = _compute_chunk_metadata(chunks, full_path_str)

    await _add_chunks_to_collection(
        collection, collection_lock, chunks, metas, max_batch_size
    )

    if num_existing_chunks:
        await _update_stats(stats, stats_lock, "update")
    else:
        await _update_stats(stats, stats_lock, "add")


async def chunk_and_vectorise_core(
    project_dir: Path,
    pattern: str,
    config: chunker_model.ChunkAndVectoriseConfig,
    logger_instance: logging.Logger,
):
    """
    Core logic for chunking and vectorising files in a project directory.

    Args:
        project_dir (Path): The root directory of the project.
        pattern (str): Glob pattern for files to process.
        config (chunker_model.ChunkAndVectoriseConfig): Configuration object for chunking and vectorising.

    Returns:
        None
    """
    # Check if pattern is missing or misused
    if pattern.startswith("--"):
        raise ValueError("The first argument must be the file pattern (e.g., '*.py').")

    # Validate language
    if config.language.lower() not in [l.name.lower() for l in Language]:
        raise ValueError(
            f"'{config.language}' is not a supported language. "
            f"Choose from: {', '.join(l.name.lower() for l in Language)}"
        )

    files = list(project_dir.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No files found matching pattern: {pattern}")

    for f in files:
        try:
            if not Path(f).resolve().is_relative_to(project_dir.resolve()):
                raise ValueError(
                    f"File {f} is outside the project directory {project_dir}"
                )
        except AttributeError:
            # For Python < 3.9, is_relative_to is not available
            try:
                f.resolve().relative_to(project_dir.resolve())
            except ValueError:
                raise ValueError(
                    f"File {f} is outside the project directory {project_dir}"
                )

    # Setup Chroma async HTTP client
    client = await chromadb.AsyncHttpClient(
        host=config.chroma_host,
        port=config.chroma_port,
    )

    try:
        collection = await client.get_or_create_collection(config.collection_name)
    except Exception as e:
        logger_instance.error(f"Failed to get/create the collection: {e}")
        raise SystemExit(1)

    stats = {"add": 0, "update": 0, "removed": 0}
    collection_lock = asyncio.Lock()
    stats_lock = asyncio.Lock()
    semaphore = asyncio.Semaphore(os.cpu_count() or 1)

    logger_instance.info(f"Starting vectorisation for {len(files)} files.")
    for file in files:
        await add_file_with_langchain(
            str(file),
            logger_instance,
            collection,
            collection_lock,
            stats,
            stats_lock,
            config.max_batch_size,
            semaphore,
            language=config.language,
        )
        logger_instance.info(f"Finished processing {file}")

    logger_instance.info(
        f"All files processed. Added: {stats['add']}, Updated: {stats['update']}"
    )

import asyncio
import os
import uuid
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language
import chromadb
import logging
from typing import Union
from chunker_src import model as chunker_model

PathLike = Union[str, Path]

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def get_uuid() -> str:
    return uuid.uuid4().hex


def expand_path(path: PathLike, absolute: bool = False) -> PathLike:
    expanded = os.path.expanduser(os.path.expandvars(path))
    if absolute:
        return os.path.abspath(expanded)
    return expanded


async def add_file_with_langchain(
    file_path: str,
    collection,
    collection_lock,
    stats: dict[str, int],
    stats_lock,
    max_batch_size: int,
    semaphore: asyncio.Semaphore,
    language: str = "python",
):
    """
    Add a file's contents to a ChromaDB collection, chunked and with metadata.

    Args:
        file_path (str): Path to the file to process.
        collection: The ChromaDB collection object.
        collection_lock: Asyncio lock for collection operations.
        stats (dict[str, int]): Dictionary to track add/update stats.
        stats_lock: Asyncio lock for stats.
        max_batch_size (int): Maximum batch size for collection.add().
        semaphore (asyncio.Semaphore): Semaphore to limit concurrency.
        language (str): Programming language for chunking.

    Returns:
        None
    """
    full_path_str = str(expand_path(str(file_path), True))
    logger.info(f"Processing file: {full_path_str}")

    # Check for existing chunks and delete if present
    async with collection_lock:
        existing = await collection.get(
            where={"path": full_path_str},
            include=["metadatas"],
        )
        num_existing_chunks = len(existing["ids"]) if "ids" in existing else 0

        if num_existing_chunks:
            await collection.delete(where={"path": full_path_str})

    try:
        async with semaphore:
            with open(full_path_str, "r", encoding="utf-8") as f:
                code = f.read()
            splitter = RecursiveCharacterTextSplitter.from_language(
                getattr(Language, language.upper())
            )
            logger.info(f"Chunking file {full_path_str} with language '{language}'")
            chunks = splitter.split_text(code)
            logger.info(f"Created {len(chunks)} chunks for {full_path_str}")
            if len(chunks) == 0 or (len(chunks) == 1 and chunks[0] == ""):
                return

            # Compute line ranges for each chunk
            lines = code.splitlines()
            metas = []
            current_line = 0
            for chunk in chunks:
                chunk_lines = chunk.count("\n") + 1
                start_line = current_line
                end_line = current_line + chunk_lines - 1
                metas.append(
                    {"path": full_path_str, "start": start_line, "end": end_line}
                )
                current_line = end_line + 1

            async with collection_lock:
                for idx in range(0, len(chunks), max_batch_size):
                    inserted_chunks = chunks[idx : idx + max_batch_size]
                    logger.info(
                        f"Adding {len(inserted_chunks)} chunks to collection for {full_path_str}"
                    )
                    await collection.add(
                        ids=[get_uuid() for _ in inserted_chunks],
                        documents=inserted_chunks,
                        metadatas=metas[idx : idx + max_batch_size],
                    )
    except UnicodeDecodeError:
        logger.warning(
            f"UnicodeDecodeError: Skipping file {full_path_str} (probably binary)"
        )
        return

    if num_existing_chunks:
        async with stats_lock:
            stats["update"] += 1
    else:
        async with stats_lock:
            stats["add"] += 1


async def chunk_and_vectorise_core(
    project_dir: Path,
    pattern: str,
    config: chunker_model.ChunkAndVectoriseConfig,
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

    # Get or create collection
    try:
        collection = await client.get_or_create_collection(config.collection_name)
    except Exception as e:
        logger.error(f"Failed to get/create the collection: {e}")
        raise SystemExit(1)

    stats = {"add": 0, "update": 0, "removed": 0}
    collection_lock = asyncio.Lock()
    stats_lock = asyncio.Lock()
    semaphore = asyncio.Semaphore(os.cpu_count() or 1)

    logger.info(f"Starting vectorisation for {len(files)} files.")
    for file in files:
        await add_file_with_langchain(
            str(file),
            collection,
            collection_lock,
            stats,
            stats_lock,
            config.max_batch_size,
            semaphore,
            language=config.language,
        )
        logger.info(f"Finished processing {file}")

    logger.info(
        f"All files processed. Added: {stats['add']}, Updated: {stats['update']}"
    )

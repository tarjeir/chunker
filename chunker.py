import typer
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language
import asyncio
import os
import uuid
from chromadb.api.types import IncludeEnum
from vectorcode.cli_utils import Config, expand_path
from vectorcode.common import get_client, get_collection, verify_ef

app = typer.Typer()

def get_uuid() -> str:
    return uuid.uuid4().hex

async def add_file_with_langchain(
    file_path: str,
    collection,
    collection_lock,
    stats: dict[str, int],
    stats_lock,
    configs: Config,
    max_batch_size: int,
    semaphore: asyncio.Semaphore,
    language: str = "python",
):
    full_path_str = str(expand_path(str(file_path), True))
    async with collection_lock:
        num_existing_chunks = len(
            (
                await collection.get(
                    where={"path": full_path_str},
                    include=[IncludeEnum.metadatas],
                )
            )["ids"]
        )

    if num_existing_chunks:
        async with collection_lock:
            await collection.delete(where={"path": full_path_str})

    try:
        async with semaphore:
            with open(full_path_str, "r", encoding="utf-8") as f:
                code = f.read()
            splitter = RecursiveCharacterTextSplitter.from_language(
                getattr(Language, language.upper())
            )
            chunks = splitter.split_text(code)
            if len(chunks) == 0 or (len(chunks) == 1 and chunks[0] == ""):
                return
            metas = [{"path": full_path_str} for _ in chunks]
            async with collection_lock:
                for idx in range(0, len(chunks), max_batch_size):
                    inserted_chunks = chunks[idx : idx + max_batch_size]
                    await collection.add(
                        ids=[get_uuid() for _ in inserted_chunks],
                        documents=inserted_chunks,
                        metadatas=metas[idx : idx + max_batch_size],
                    )
    except UnicodeDecodeError:
        return

    if num_existing_chunks:
        async with stats_lock:
            stats["update"] += 1
    else:
        async with stats_lock:
            stats["add"] += 1

async def langchain_vectorise(configs: Config, language: str = "python") -> int:
    assert configs.project_root is not None
    client = await get_client(configs)
    try:
        collection = await get_collection(client, configs, True)
    except IndexError:
        print("Failed to get/create the collection. Please check your config.")
        return 1
    if not verify_ef(collection, configs):
        return 1

    files = configs.files

    stats = {"add": 0, "update": 0, "removed": 0}
    collection_lock = asyncio.Lock()
    stats_lock = asyncio.Lock()
    max_batch_size = await client.get_max_batch_size()
    semaphore = asyncio.Semaphore(os.cpu_count() or 1)

    for file in files:
        await add_file_with_langchain(
            str(file),
            collection,
            collection_lock,
            stats,
            stats_lock,
            configs,
            max_batch_size,
            semaphore,
            language=language,
        )
        print(f"Processed {file}")

    print(f"Added: {stats['add']}, Updated: {stats['update']}")
    return 0

@app.command()
def chunk_and_vectorise(
    pattern: str = typer.Argument(
        ..., help="Glob pattern for files to process (e.g., '*.py')"
    ),
    language: str = typer.Option(
        "python", help="Programming language for splitting (e.g., 'python')"
    ),
):
    files = list(Path(".").glob(pattern))
    if not files:
        typer.echo(f"No files found matching pattern: {pattern}")
        raise typer.Exit(code=1)

    configs = Config()
    configs.files = [str(f) for f in files]
    configs.project_root = str(Path(".").resolve())

    asyncio.run(langchain_vectorise(configs, language=language))


if __name__ == "__main__":
    app()

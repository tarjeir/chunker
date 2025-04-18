import typer
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language
import asyncio
import os
import uuid
from chromadb.api.types import IncludeEnum
from vectorcode.cli_utils import Config, expand_path
from vectorcode.common import get_client, get_collection, verify_ef
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

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
    logger.info(f"Processing file: {full_path_str}")
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


@app.command()
def chunk_and_vectorise(
    project_dir: Path = typer.Argument(
        ..., help="Root directory of the project to search for files"
    ),
    pattern: str = typer.Argument(
        ..., help="Glob pattern for files to process (e.g., '*.py')"
    ),
    language: str = typer.Option(
        "python", help="Programming language for splitting (e.g., 'python')"
    ),
):
    # Check if pattern is missing or misused
    if pattern.startswith("--"):
        typer.echo(
            "Error: The first argument must be the file pattern (e.g., '*.py').",
            err=True,
        )
        raise typer.Exit(code=2)

    # Validate language
    from langchain_text_splitters import Language

    if language.lower() not in [l.name.lower() for l in Language]:
        typer.echo(
            f"Error: '{language}' is not a supported language. "
            f"Choose from: {', '.join(l.name.lower() for l in Language)}",
            err=True,
        )
        raise typer.Exit(code=2)

    files = list(project_dir.glob(pattern))
    if not files:
        typer.echo(f"No files found matching pattern: {pattern}")
        raise typer.Exit(code=1)

    for f in files:
        try:
            if not Path(f).resolve().is_relative_to(project_dir.resolve()):
                typer.echo(
                    f"Error: File {f} is outside the project directory {project_dir}",
                    err=True,
                )
                raise typer.Exit(code=2)
        except AttributeError:
            # For Python < 3.9, is_relative_to is not available
            try:
                f.resolve().relative_to(project_dir.resolve())
            except ValueError:
                typer.echo(
                    f"Error: File {f} is outside the project directory {project_dir}",
                    err=True,
                )
                raise typer.Exit(code=2)

    configs = Config()
    configs.files = [str(f) for f in files]
    configs.project_root = str(project_dir.resolve())

    async def main():
        assert configs.project_root is not None
        client = await get_client(configs)
        try:
            collection = await get_collection(client, configs, True)
        except IndexError:
            print("Failed to get/create the collection. Please check your config.")
            raise typer.Exit(code=1)
        if not verify_ef(collection, configs):
            raise typer.Exit(code=1)

        stats = {"add": 0, "update": 0, "removed": 0}
        collection_lock = asyncio.Lock()
        stats_lock = asyncio.Lock()
        max_batch_size = await client.get_max_batch_size()
        semaphore = asyncio.Semaphore(os.cpu_count() or 1)

        logger.info(f"Starting vectorisation for {len(configs.files)} files.")
        for file in configs.files:
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
            logger.info(f"Finished processing {file}")

        logger.info(
            f"All files processed. Added: {stats['add']}, Updated: {stats['update']}"
        )

    asyncio.run(main())


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def chunk_and_vectorise_mcp(ctx: typer.Context):
    import sys
    from chunker import main as chunker_mcp_main

    sys.argv = [sys.argv[0]] + ctx.args

    chunker_mcp_main()


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def vectorcode_cli(ctx: typer.Context):
    import sys
    from vectorcode import main

    sys.argv = [sys.argv[0]] + ctx.args
    main.main()


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def vectorcode_mcp(ctx: typer.Context):
    import sys
    from vectorcode import mcp_main

    sys.argv = [sys.argv[0]] + ctx.args
    mcp_main.main()


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def vectorcode_lsp(ctx: typer.Context):
    import sys
    from vectorcode import lsp_main

    sys.argv = [sys.argv[0]] + ctx.args
    lsp_main.main()


if __name__ == "__main__":
    app()

import asyncio
import typer
from pathlib import Path
import logging
import json
from chunker_src.chunk_and_vectorise import chunk_and_vectorise_core
from chunker_src import model as chunker_model
from chunker_src.query_chunks import query_chunks_core
from chunker_src.crud import delete_all_records_in_collection

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

app = typer.Typer()


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
    chroma_host: str = typer.Option(
        "localhost", help="ChromaDB host (default: 'localhost')"
    ),
    chroma_port: int = typer.Option(8000, help="ChromaDB port (default: 8000)"),
    collection_name: str = typer.Option(
        "default", help="ChromaDB collection name (default: 'default')"
    ),
    max_batch_size: int = typer.Option(
        64, help="Maximum batch size for collection.add() (default: 64)"
    ),
):
    config = chunker_model.ChunkAndVectoriseConfig(
        chroma_host=chroma_host,
        chroma_port=chroma_port,
        collection_name=collection_name,
        max_batch_size=max_batch_size,
        language=language,
    )
    result = asyncio.run(
        chunk_and_vectorise_core(
            project_dir=project_dir,
            pattern=pattern,
            config=config,
            logger_instance=logger,
        )
    )
    if result is None:
        typer.echo(
            f"Chunked and vectorised files matching: {pattern} (language: {language})"
        )
    else:
        typer.echo(f"Error: {getattr(result, 'message', str(result))}", err=True)
        raise typer.Exit(code=2)


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def chunk_and_vectorise_mcp(ctx: typer.Context):
    import sys
    from chunker_src.chunker_mcp import main as chunker_mcp_main

    sys.argv = [sys.argv[0]] + ctx.args

    chunker_mcp_main()


@app.command()
def query_chunks(
    query: str = typer.Argument(
        ..., help="Query string to search for in the collection"
    ),
    chroma_host: str = typer.Option(
        "localhost", help="ChromaDB host (default: 'localhost')"
    ),
    chroma_port: int = typer.Option(8000, help="ChromaDB port (default: 8000)"),
    collection_name: str = typer.Option(
        "default", help="ChromaDB collection name (default: 'default')"
    ),
    n_results: int = typer.Option(10, help="Number of results to return (default: 10)"),
):
    """
    Query chunks from a ChromaDB collection and print the results as JSON.

    Args:
        query (str): The query string to search for.
        chroma_host (str): ChromaDB host.
        chroma_port (int): ChromaDB port.
        collection_name (str): ChromaDB collection name.
        n_results (int): Number of results to return.
    """

    logger = logging.getLogger(__name__)

    if n_results < 1:
        typer.echo("Error: n_results must be at least 1.", err=True)
        raise typer.Exit(code=2)

    config = chunker_model.QueryChunksConfig(
        chroma_host=chroma_host,
        chroma_port=chroma_port,
        collection_name=collection_name,
        n_results=n_results,
    )

    try:
        result = asyncio.run(
            query_chunks_core(
                query_text=query,
                config=config,
                logger=logger,
                n_results=n_results,
            )
        )
        if not result:
            typer.echo("No results found.")
        else:
            json_result = json.dumps([r.model_dump_json() for r in result], indent=2)
            typer.echo(json_result)
    except Exception as e:
        typer.echo(f"Error during query: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def delete_collection(
    chroma_host: str = typer.Option(
        "localhost", help="ChromaDB host (default: 'localhost')"
    ),
    chroma_port: int = typer.Option(8000, help="ChromaDB port (default: 8000)"),
    collection_name: str = typer.Option(
        "default", help="ChromaDB collection name (default: 'default')"
    ),
):
    """
    Delete all records in a specific ChromaDB collection.

    Args:
        chroma_host (str): ChromaDB host.
        chroma_port (int): ChromaDB port.
        collection_name (str): ChromaDB collection name.
    """
    try:
        asyncio.run(
            delete_all_records_in_collection(
                chroma_host=chroma_host,
                chroma_port=chroma_port,
                collection_name=collection_name,
            )
        )
        typer.echo(f"All records deleted from collection '{collection_name}'.")
    except Exception as e:
        typer.echo(f"Error deleting collection: {e}", err=True)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()

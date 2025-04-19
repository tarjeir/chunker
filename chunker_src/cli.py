import asyncio
import typer
from pathlib import Path
import logging
from chunker_src.chunk_and_vectorise import chunk_and_vectorise_core
from chunker_src import model as chunker_model

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
        None, help="ChromaDB host (default: 'localhost')"
    ),
    chroma_port: int = typer.Option(
        None, help="ChromaDB port (default: 8000)"
    ),
    collection_name: str = typer.Option(
        None, help="ChromaDB collection name (default: 'default')"
    ),
    max_batch_size: int = typer.Option(
        None, help="Maximum batch size for collection.add() (default: 64)"
    ),
):
    config = chunker_model.ChunkAndVectoriseConfig(
        chroma_host=chroma_host or chunker_model.ChunkAndVectoriseConfig.chroma_host,
        chroma_port=chroma_port or chunker_model.ChunkAndVectoriseConfig.chroma_port,
        collection_name=collection_name or chunker_model.ChunkAndVectoriseConfig.collection_name,
        max_batch_size=max_batch_size or chunker_model.ChunkAndVectoriseConfig.max_batch_size,
        language=language,
    )
    try:
        asyncio.run(
            chunk_and_vectorise_core(
                project_dir=project_dir,
                pattern=pattern,
                config=config,
                logger_instance=logger,
            )
        )
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=2)
    except FileNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)
    except SystemExit as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=2)


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def chunk_and_vectorise_mcp(ctx: typer.Context):
    import sys
    from chunker_src.chunker_mcp import main as chunker_mcp_main

    sys.argv = [sys.argv[0]] + ctx.args

    chunker_mcp_main()




if __name__ == "__main__":
    app()

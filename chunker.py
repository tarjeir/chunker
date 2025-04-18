import typer
from pathlib import Path
import asyncio
import os
from chromadb.api.types import IncludeEnum
from vectorcode.cli_utils import Config, expand_path
from vectorcode.common import get_client, get_collection, verify_ef
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

app = typer.Typer()

from chunker.chunk_and_vectorise import chunk_and_vectorise_core


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
    chroma_host: str = typer.Option(None, help="ChromaDB host "),
    chroma_port: int = typer.Option(None, help="ChromaDB port "),
):
    try:
        chunk_and_vectorise_core(
            project_dir=project_dir,
            pattern=pattern,
            language=language,
            chroma_host=chroma_host,
            chroma_port=chroma_port,
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
    from chunker.chunker_mcp import main as chunker_mcp_main

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

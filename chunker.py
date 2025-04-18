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

from chunker.chunk_and_vectorise import chunk_and_vectorise

# Register the imported command with the Typer app
# If chunk_and_vectorise is decorated with @app.command() in the imported module,
# this import is enough to register it.
# Otherwise, uncomment the next line to register it explicitly:
# app.command()(chunk_and_vectorise)


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

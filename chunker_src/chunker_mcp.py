import argparse
from fastmcp import FastMCP, Context
import os
from fastmcp.prompts.prompt import UserMessage, AssistantMessage
from pathlib import Path
from chunker_src.chunk_and_vectorise import chunk_and_vectorise_core
import logging
from chunker_src import model as chunker_model

mcp = FastMCP("Chunker MCP")


@mcp.tool()
async def chunk_and_vectorise(
    pattern: str,
    language: str,
    ctx: Context,
) -> str:
    """
    Chunk and vectorise files matching the given pattern and language.
    `project_dir` is the root directory of the project to search for files.
    `chroma_host` and `chroma_port` specify the Chroma DB connection.
    """
    project_dir = os.environ.get("PROJECT_DIR")
    chroma_host = os.environ.get("CHROMA_HOST")
    chroma_port = os.environ.get("CHROMA_PORT")
    collection_name = os.environ.get("CHROMA_COLLECTION_NAME", "default")
    max_batch_size = os.environ.get("CHROMA_MAX_BATCH_SIZE", "64")

    if not project_dir:
        await ctx.log("error", "Error: project_dir must be specified.")
        return "Error: project_dir must be specified."
    if not chroma_host:
        await ctx.log("error", "Error: chroma_host must be specified.")
        return "Error: chroma_host must be specified."
    if not chroma_port:
        await ctx.log("error", "Error: chroma_port must be specified.")
        return "Error: chroma_port must be specified."

    try:
        chroma_port_int = int(chroma_port)
    except Exception:
        await ctx.log("error", f"Error: chroma_port must be an integer, got {chroma_port!r}")
        return f"Error: chroma_port must be an integer, got {chroma_port!r}"

    try:
        max_batch_size_int = int(max_batch_size)
    except Exception:
        await ctx.log("error", f"Error: max_batch_size must be an integer, got {max_batch_size!r}")
        return f"Error: max_batch_size must be an integer, got {max_batch_size!r}"

    config = chunker_model.ChunkAndVectoriseConfig(
        chroma_host=chroma_host,
        chroma_port=chroma_port_int,
        collection_name=collection_name,
        max_batch_size=max_batch_size_int,
        language=language,
    )

    logger = logging.getLogger(__name__)

    try:
        await chunk_and_vectorise_core(
            Path(project_dir),
            pattern,
            config,
            logger_instance=logger,
        )
        await ctx.log(
            "info",
            f"Chunked and vectorised files matching: {pattern} (language: {language})",
        )
        return (
            f"Chunked and vectorised files matching: {pattern} (language: {language})"
        )
    except SystemExit as e:
        await ctx.log("error", f"Error: {e}")
        return f"Error: {e}"
    except Exception as e:
        await ctx.log("error", f"Unexpected error: {e}")
        return f"Unexpected error: {e}"


@mcp.prompt()
def pattern_help() -> str:
    """
    Explains how to write file patterns for chunking and vectorising.
    """
    return (
        "To specify which files to chunk and vectorise, use a glob pattern. "
        "For example:\n"
        "- '*.py' matches all Python files in the current directory.\n"
        "- '**/*.js' matches all JavaScript files in this directory and subdirectories.\n"
        "- 'src/**/*.ts' matches all TypeScript files under the 'src' folder.\n"
        "You can use any valid Unix-style glob pattern."
    )


@mcp.prompt()
def example_patterns() -> list:
    """
    Provides example file patterns for common use cases.
    """
    return [
        UserMessage("How do I select all Python files in my project?"),
        AssistantMessage(
            "Use the pattern '**/*.py' to match all Python files recursively."
        ),
        UserMessage("How do I select only files in the current directory?"),
        AssistantMessage(
            "Use '*.py' to match all Python files in the current directory only."
        ),
        UserMessage("How do I select all Markdown files in a docs folder?"),
        AssistantMessage(
            "Use 'docs/**/*.md' to match all Markdown files under the docs directory."
        ),
    ]


@mcp.prompt()
def language_help() -> str:
    """
    Explains how to choose the language for chunking and vectorising.
    """
    return (
        "Specify the programming language of the files you want to chunk and vectorise using the --language option. "
        "Supported languages are:\n"
        "- cpp\n"
        "- go\n"
        "- java\n"
        "- kotlin\n"
        "- js\n"
        "- ts\n"
        "- php\n"
        "- proto\n"
        "- python\n"
        "- rst\n"
        "- ruby\n"
        "- rust\n"
        "- scala\n"
        "- swift\n"
        "- markdown\n"
        "- latex\n"
        "- html\n"
        "- sol\n"
        "- csharp\n"
        "- cobol\n"
        "- c\n"
        "- lua\n"
        "- perl\n"
        "- haskell\n"
        "- elixir\n"
        "- powershell\n"
        "Example: Use '--language python' for Python files, or '--language js' for JavaScript files."
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project_dir", type=str, required=True)
    parser.add_argument("--chroma_host", type=str, default=None)
    parser.add_argument("--chroma_port", type=int, default=None)
    args, _ = parser.parse_known_args()

    os.environ["PROJECT_DIR"] = args.project_dir
    os.environ["CHROMA_HOST"] = args.chroma_host or "127.0.0.1"
    os.environ["CHROMA_PORT"] = str(args.chroma_port) if args.chroma_port else "8000"
    mcp.run()

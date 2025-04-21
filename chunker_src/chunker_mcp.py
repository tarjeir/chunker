import argparse
from chunker_src.crud import delete_all_records_in_collection
from fastmcp import FastMCP, Context
import os
from fastmcp.prompts.prompt import UserMessage, AssistantMessage
from pathlib import Path
from chunker_src.chunk_and_vectorise import chunk_and_vectorise_core
from chunker_src.query_chunks import query_chunks_core
import logging
from chunker_src import model as chunker_model
import sys
from typing import Any, Literal
import pathspec


mcp = FastMCP("Chunker MCP")


def _parse_gitignore(project_dir: Path) -> pathspec.PathSpec | None:
    """
    Parse the .gitignore file in the project directory and return a PathSpec object.

    Args:
        project_dir (Path): The root directory of the project.

    Returns:
        PathSpec | None: The PathSpec object if .gitignore exists, else None.
    """
    gitignore_path = project_dir / ".gitignore"
    if gitignore_path.exists():
        with open(gitignore_path, "r", encoding="utf-8") as f:
            gitignore_patterns = f.read().splitlines()
        return pathspec.PathSpec.from_lines("gitwildmatch", gitignore_patterns)
    return None


def _traverse_project_dir_and_ignore_dirs(
    base: Path, spec: pathspec.PathSpec | None, recursive: bool = False
) -> list[Path]:
    """
    Traverse the project directory and return a list of directories,
    excluding those ignored by .gitignore and .git.

    Args:
        base (Path): The root directory of the project.
        spec (PathSpec | None): The PathSpec object for .gitignore, or None.
        recursive (bool): Whether to traverse recursively.

    Returns:
        list[Path]: List of relative directory paths.
    """
    dirs = []
    if recursive:
        for root, dirnames, _ in os.walk(base):
            rel_root = Path(root).relative_to(base)

            def is_ignored_dir(rel_path: Path) -> bool:
                if not spec:
                    return False
                rel_str = rel_path.as_posix()
                return spec.match_file(rel_str) or spec.match_file(rel_str + "/")

            dirnames[:] = [
                d for d in dirnames if d != ".git" and not is_ignored_dir(rel_root / d)
            ]
            for d in dirnames:
                dirs.append(rel_root / d)
    else:
        for d in base.iterdir():
            if d.is_dir() and d.name != ".git":
                rel_path = d.relative_to(base)
                if not (
                    spec
                    and (
                        spec.match_file(str(rel_path.as_posix()))
                        or spec.match_file(str(rel_path.as_posix()) + "/")
                    )
                ):
                    dirs.append(rel_path)
    return dirs


@mcp.tool(
    description="Chunk and vectorise files matching the given pattern and language.",
)
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
    collection_name = os.environ.get("CHROMA_COLLECTION_NAME")
    max_batch_size = os.environ.get("CHROMA_MAX_BATCH_SIZE", "64")
    language = os.environ.get("LANGUAGE", "python")

    if not project_dir:
        await ctx.log("error", "Error: project_dir must be specified.")
        return "Error: project_dir must be specified."
    if not chroma_host:
        await ctx.log("error", "Error: chroma_host must be specified.")
        return "Error: chroma_host must be specified."
    if not chroma_port:
        await ctx.log("error", "Error: chroma_port must be specified.")
        return "Error: chroma_port must be specified."
    if not collection_name:
        await ctx.log("error", "Error: chroma_collection_name must be specified.")
        return "Error: chroma_collection_name must be specified."

    try:
        chroma_port_int = int(chroma_port)
    except Exception:
        await ctx.log(
            "error", f"Error: chroma_port must be an integer, got {chroma_port!r}"
        )
        return f"Error: chroma_port must be an integer, got {chroma_port!r}"

    try:
        max_batch_size_int = int(max_batch_size)
    except Exception:
        await ctx.log(
            "error", f"Error: max_batch_size must be an integer, got {max_batch_size!r}"
        )
        return f"Error: max_batch_size must be an integer, got {max_batch_size!r}"

    config = chunker_model.ChunkAndVectoriseConfig(
        chroma_host=chroma_host,
        chroma_port=chroma_port_int,
        collection_name=collection_name,
        max_batch_size=max_batch_size_int,
        language=language,
    )

    logger = logging.getLogger(__name__)

    result = await chunk_and_vectorise_core(
        Path(project_dir),
        pattern,
        config,
        logger_instance=logger,
    )
    if result is None:
        await ctx.log(
            "info",
            f"Chunked and vectorised files matching: {pattern} (language: {language})",
        )
        return (
            f"Chunked and vectorised files matching: {pattern} (language: {language})"
        )
    else:
        await ctx.log("error", f"Error: {getattr(result, 'message', str(result))}")
        return f"Error: {getattr(result, 'message', str(result))}"


@mcp.tool(
    description="Query chunks from the ChromaDB collection using the provided query string.",
)
async def query_chunks(
    query: str,
    ctx: Context,
) -> str:
    """
    Query chunks from the ChromaDB collection using the provided query string.
    All configuration is loaded from environment variables.

    Args:
        query (str): The query string to search for.
        ctx (Context): The MCP context for logging.

    Returns:
        str: A summary of the query result or an error message.
    """
    import os
    import logging

    chroma_host = os.environ.get("CHROMA_HOST")
    chroma_port = os.environ.get("CHROMA_PORT")
    collection_name = os.environ.get("CHROMA_COLLECTION_NAME")
    n_results = os.environ.get("CHROMA_N_RESULTS", "10")

    if not chroma_host:
        await ctx.log("error", "Error: chroma_host must be specified.")
        return "Error: chroma_host must be specified."
    if not chroma_port:
        await ctx.log("error", "Error: chroma_port must be specified.")
        return "Error: chroma_port must be specified."
    if not collection_name:
        await ctx.log("error", "Error: chroma_collection_name must be specified.")
        return "Error: chroma_collection_name must be specified."

    try:
        chroma_port_int = int(chroma_port)
    except Exception:
        msg = f"Error: CHROMA_PORT must be an integer, got {chroma_port!r}"
        await ctx.log("error", msg)
        return msg

    try:
        n_results_int = int(n_results)
    except Exception:
        msg = f"Error: CHROMA_N_RESULTS must be an integer, got {n_results!r}"
        await ctx.log("error", msg)
        return msg

    config = chunker_model.QueryChunksConfig(
        chroma_host=chroma_host,
        chroma_port=chroma_port_int,
        collection_name=collection_name,
        n_results=n_results_int,
    )

    logger = logging.getLogger(__name__)

    try:
        result = await query_chunks_core(
            query_text=query,
            config=config,
            logger=logger,
            n_results=n_results_int,
        )
        summary = "["
        for r in result:
            summary += r.model_dump_json()
            summary += ","
        summary += "]"

        await ctx.log("info", summary)
        return summary
    except Exception as e:
        msg = f"Error during query: {e}"
        await ctx.log("error", msg)
        return msg


@mcp.tool(
    description="Delete all records in the specified ChromaDB collection.",
)
async def delete_collection(
    ctx: Context,
) -> str:
    """
    Delete all records in the specified ChromaDB collection.

    Args:
        ctx (Context): The MCP context for logging.

    Returns:
        str: Success or error message.
    """
    import os

    chroma_host = os.environ.get("CHROMA_HOST")
    chroma_port = os.environ.get("CHROMA_PORT")
    collection_name = os.environ.get("CHROMA_COLLECTION_NAME")
    if not collection_name:
        await ctx.log("error", "Error: collection_name must be specified.")
        return "Error: collection_name must be specified."
    if not chroma_host:
        await ctx.log("error", "Error: chroma_host must be specified.")
        return "Error: chroma_host must be specified."
    if not chroma_port:
        await ctx.log("error", "Error: chroma_port must be specified.")
        return "Error: chroma_port must be specified."
    try:
        chroma_port_int = int(chroma_port)
    except Exception:
        await ctx.log(
            "error", f"Error: chroma_port must be an integer, got {chroma_port!r}"
        )
        return f"Error: chroma_port must be an integer, got {chroma_port!r}"

    if not collection_name:
        await ctx.log(
            "error",
            "Error: collection_name must be specified (argument, global, or env).",
        )
        return "Error: collection_name must be specified (argument, global, or env)."

    try:
        await delete_all_records_in_collection(
            chroma_host=chroma_host,
            chroma_port=chroma_port_int,
            collection_name=collection_name,
        )
        await ctx.log(
            "info", f"All records deleted from collection '{collection_name}'."
        )
        return f"All records deleted from collection '{collection_name}'."
    except Exception as e:
        await ctx.log("error", f"Error deleting collection: {e}")
        return f"Error deleting collection: {e}"


@mcp.tool(
    description="List directories in the project directory, excluding those ignored by .gitignore and .git.",
)
async def list_project_directories(
    ctx: Context,
    recursive: bool = False,
) -> str:
    """
    List all directories in the project directory, excluding those ignored by .gitignore and .git.

    Args:
        ctx (Context): The MCP context for logging.
        recursive (bool, optional): Whether to list directories recursively. Default is False.

    Returns:
        str: A newline-separated list of directories, or an error message.
    """
    project_dir = os.environ.get("PROJECT_DIR")
    if not project_dir:
        await ctx.log("error", "Error: PROJECT_DIR must be specified.")
        return "Error: PROJECT_DIR must be specified."

    base = Path(project_dir)
    if not base.exists() or not base.is_dir():
        await ctx.log(
            "error", f"Error: PROJECT_DIR '{project_dir}' is not a valid directory."
        )
        return f"Error: PROJECT_DIR '{project_dir}' is not a valid directory."

    spec = _parse_gitignore(base)
    dirs = _traverse_project_dir_and_ignore_dirs(base, spec, recursive=recursive)

    if not dirs:
        await ctx.log("info", "No directories found in the project directory.")
        return "No directories found in the project directory."

    dir_list = "\n".join(str(d) for d in sorted(dirs))
    await ctx.log("info", f"Found directories:\n{dir_list}")
    return f"Found directories:\n{dir_list}"


@mcp.tool(
    description="Read the contents of a single file by relative path from the project directory.",
)
async def read_file(
    relative_path: str,
    ctx: Context,
) -> str:
    """
    Reads the contents of a single file given a relative path from the project directory.

    Args:
        relative_path (str): The path to the file, relative to the project root.
        ctx (Context): The MCP context for logging.

    Returns:
        str: The file contents, or an error message.
    """
    import os

    project_dir = os.environ.get("PROJECT_DIR")
    if not project_dir:
        await ctx.log("error", "Error: PROJECT_DIR must be specified.")
        return "Error: PROJECT_DIR must be specified."

    base = Path(project_dir)
    file_path = base / relative_path

    # Security: ensure the resolved path is within the project directory
    try:
        file_path_resolved = file_path.resolve(strict=True)
        base_resolved = base.resolve(strict=True)
        if not str(file_path_resolved).startswith(str(base_resolved)):
            await ctx.log("error", "Error: File is outside the project directory.")
            return "Error: File is outside the project directory."
    except FileNotFoundError:
        await ctx.log("error", f"Error: File '{relative_path}' does not exist.")
        return f"Error: File '{relative_path}' does not exist."

    if not file_path.is_file():
        await ctx.log("error", f"Error: '{relative_path}' is not a file.")
        return f"Error: '{relative_path}' is not a file."

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            contents = f.read()
        await ctx.log("info", f"Read file '{relative_path}' successfully.")
        return contents
    except Exception as e:
        await ctx.log("error", f"Error reading file: {e}")
        return f"Error reading file: {e}"


@mcp.prompt(name="chunk_and_vectorise")
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


@mcp.prompt(name="chunk_and_vectorise")
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


@mcp.prompt(name="chunk_and_vectorise")
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


@mcp.prompt(name="chunk_and_vectorise")
def good_pattern_help() -> str:
    """
    Explains what makes a good file pattern for chunking and vectorising, including enforced rules.
    """
    return (
        "A good file pattern is specific, safe, and efficient. The following rules are strictly enforced:\n"
        "\n"
        "Forbidden patterns:\n"
        "- Patterns containing '..' are not allowed (no parent directory traversal).\n"
        "- Patterns that are exactly '**' or start with '**/' are not allowed (no recursive all-file matches).\n"
        "\n"
        "Allowed patterns must:\n"
        "- Be relative to the project root directory.\n"
        "- Be as specific as possible to avoid matching too many files.\n"
        "- Match only the file types you want to process (e.g., '*.py', 'src/**/*.js').\n"
        "\n"
        "Examples of allowed patterns:\n"
        "- '*.py' (all Python files in the root directory)\n"
        "- 'src/*.js' (all JavaScript files in the 'src' directory)\n"
        "- 'docs/**/*.md' (all Markdown files in the 'docs' folder and subfolders)\n"
        "\n"
        "Examples of forbidden patterns:\n"
        "- '../*.py' (parent directory traversal is not allowed)\n"
        "- '**' (recursive all-file match is not allowed)\n"
        "- '**/*.py' (recursive all-file match is not allowed)\n"
        "- '**/foo.py' (recursive all-file match is not allowed)\n"
        "\n"
        "Choose patterns that help you focus on the files you want to process, while avoiding unnecessary or unsafe matches. "
        "If your pattern is rejected, check that it does not use '..' or start with '**/'."
    )


@mcp.prompt(name="read_file")
def read_file_help() -> str:
    """
    Explains how to use the read_file tool.
    """
    return (
        "Use the 'read_file' tool to read the contents of a single file by specifying its path "
        "relative to the project root directory. Only one file can be read at a time, and the path "
        "must not be an expression or glob pattern. Example: 'src/main.py'."
    )


@mcp.prompt(name="query_chunks")
def query_chunks_help() -> str:
    """
    Explains how to use the query_chunks tool.
    """
    return (
        "Use the 'query_chunks' tool to perform a semantic vector search over your project's code and documentation. "
        "This tool uses embeddings to find the most relevant code items—such as functions, classes, or docstrings—"
        "that best match your natural language query. "
        "It is optimized for code and technical documentation, so queries should focus on code concepts, usage, or structure.\n"
        "\n"
        "Arguments:\n"
        "- query: The search string or question about your codebase (e.g., function names, class responsibilities, or documentation topics).\n"
        "\n"
        "Example usage:\n"
        "- 'Where is the database connection established?'\n"
        "- 'List all classes that inherit from BaseModel.'\n"
        "- 'Show me docstrings related to authentication.'\n"
        "\n"
        "Note: This is a vector (embedding-based) search, so results are based on semantic similarity, not exact keyword matches.\n"
        "The number of results can be configured via the CHROMA_N_RESULTS environment variable (default: 10)."
    )


def main(
    transport: Literal["stdio", "sse"] | None = None,
    **transport_kwargs: Any,
) -> None:
    """
    Entry point for the Chunker MCP CLI. Ensures all required configuration
    arguments are provided and non-empty before starting the MCP server.

    Exits with an error if any required argument is missing or empty.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--project_dir", type=str, required=True)
    parser.add_argument("--chroma_host", type=str, required=True)
    parser.add_argument("--chroma_port", type=int, required=True)
    parser.add_argument("--chroma_collection_name", type=str, required=True)
    args, _ = parser.parse_known_args()

    missing = []
    if not args.project_dir or not args.project_dir.strip():
        missing.append("--project_dir")
    if not args.chroma_host or not args.chroma_host.strip():
        missing.append("--chroma_host")
    if args.chroma_port is None or str(args.chroma_port).strip() == "":
        missing.append("--chroma_port")
    if not args.chroma_collection_name or not args.chroma_collection_name.strip():
        missing.append("--chroma_collection_name")

    if missing:
        sys.stderr.write(
            f"Error: The following required arguments are missing or empty: {', '.join(missing)}\n"
        )
        sys.exit(1)

    os.environ["PROJECT_DIR"] = args.project_dir
    os.environ["CHROMA_HOST"] = args.chroma_host
    os.environ["CHROMA_PORT"] = str(args.chroma_port)
    os.environ["CHROMA_COLLECTION_NAME"] = args.chroma_collection_name
    mcp.run(transport=transport, **transport_kwargs)

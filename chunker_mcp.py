from fastmcp import FastMCP, Context
from chunker import chunk_and_vectorise as chunk_and_vectorise_cli
import typer
from fastmcp.prompts.base import UserMessage, AssistantMessage
from pathlib import Path

mcp = FastMCP("Chunker MCP")


@mcp.tool()
def chunk_and_vectorise(
    project_dir: str,
    pattern: str,
    language: str = "python",
    ctx: Context = None,
) -> str:
    """
    Chunk and vectorise files matching the given pattern and language.
    `project_dir` is the root directory of the project to search for files.
    """
    # Call the Typer CLI function directly
    try:
        chunk_and_vectorise_cli(Path(project_dir), pattern, language)
        return (
            f"Chunked and vectorised files matching: {pattern} (language: {language})"
        )
    except typer.Exit as e:
        return f"Error: {e}"



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
    mcp.run()


if __name__ == "__main__":
    main()

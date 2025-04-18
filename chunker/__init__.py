
import argparse
import os
from pathlib import Path
from fastmcp import FastMCP, Context
from fastmcp.prompts.prompt import UserMessage, AssistantMessage
from chunker import chunk_and_vectorise as chunk_and_vectorise_cli

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
    """
    project_dir = os.environ.get("PROJECT_DIR")
    if not project_dir:
        await ctx.log("error", "Error: project_dir must be specified.")
        return "Error: project_dir must be specified."
    try:
        chunk_and_vectorise_cli(Path(project_dir), pattern, language)
        await ctx.log("info", f"Chunked and vectorised files matching: {pattern} (language: {language})")
        return f"Chunked and vectorised files matching: {pattern} (language: {language})"
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
    args, _ = parser.parse_known_args()

    os.environ["PROJECT_DIR"] = args.project_dir

    mcp.run()


if __name__ == "__main__":
    main()

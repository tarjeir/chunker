from fastmcp import FastMCP, Context
from chunker import chunk_and_vectorise as chunk_and_vectorise_cli
import typer

mcp = FastMCP("Chunker MCP")

@mcp.tool()
def chunk_and_vectorise(
    pattern: str,
    language: str = "python",
    ctx: Context = None,
) -> str:
    """
    Chunk and vectorise files matching the given pattern and language.
    """
    # Call the Typer CLI function directly
    try:
        chunk_and_vectorise_cli(pattern, language)
        return f"Chunked and vectorised files matching: {pattern} (language: {language})"
    except typer.Exit as e:
        return f"Error: {e}"

def main():
    mcp.run()

if __name__ == "__main__":
    main()

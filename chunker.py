import typer
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language
from vectorcode.chunking import (
    StringChunker,
    FileChunker,
    TreeSitterChunker,
    ChunkerBase,
)
from vectorcode.cli_utils import Config
from vectorcode.vectorise import vectorise

app = typer.Typer()

# Registry of available chunkers
CHUNKER_REGISTRY = {
    "string": StringChunker,
    "file": FileChunker,
    "tree_sitter": TreeSitterChunker,
    "langchain": None,  # Special case handled below
}


@app.command()
def chunk_and_vectorise(
    pattern: str = typer.Argument(
        ..., help="Glob pattern for files to process (e.g., '*.py')"
    ),
    language: str = typer.Option(
        "python", help="Programming language for splitting (e.g., 'python')"
    ),
    chunker: str = typer.Option(
        "langchain", help="Chunker to use: string, file, tree_sitter, langchain"
    ),
):
    files = list(Path(".").glob(pattern))
    if not files:
        typer.echo(f"No files found matching pattern: {pattern}")
        raise typer.Exit(code=1)

    if chunker == "langchain":
        splitter = RecursiveCharacterTextSplitter.from_language(
            getattr(Language, language.upper())
        )
        for file_path in files:
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()
            chunks = splitter.split_text(code)
            # You may want to adapt this to your vectorise API
            vectorise(chunks)
            typer.echo(f"Processed {file_path} ({len(chunks)} chunks)")
    else:
        chunker_cls = CHUNKER_REGISTRY.get(chunker)
        if not chunker_cls:
            typer.echo(f"Unknown chunker: {chunker}")
            raise typer.Exit(code=2)
        config = Config()
        chunker_instance = chunker_cls(config)
        for file_path in files:
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()
            # For StringChunker, chunk on string; for FileChunker, chunk on file object; for TreeSitterChunker, chunk on path
            if chunker == "string":
                chunks = list(chunker_instance.chunk(code))
            elif chunker == "file":
                with open(file_path, "r", encoding="utf-8") as f2:
                    chunks = list(chunker_instance.chunk(f2))
            elif chunker == "tree_sitter":
                chunks = list(chunker_instance.chunk(str(file_path)))
            else:
                chunks = []
            # You may want to adapt this to your vectorise API
            vectorise(chunks)
            typer.echo(f"Processed {file_path} ({len(chunks)} chunks)")


if __name__ == "__main__":
    app()

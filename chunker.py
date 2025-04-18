import typer
from pathlib import Path
from vectorcode.subcommands import vectorise
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language

app = typer.Typer()


@app.command()
def chunk_and_vectorise(
    pattern: str = typer.Argument(
        ..., help="Glob pattern for files to process (e.g., '*.py')"
    ),
    language: str = typer.Option(
        "python", help="Programming language for splitting (e.g., 'python')"
    ),
):
    splitter = RecursiveCharacterTextSplitter.from_language(
        getattr(Language, language.upper())
    )
    files = list(Path(".").glob(pattern))
    if not files:
        typer.echo(f"No files found matching pattern: {pattern}")
        raise typer.Exit(code=1)
    for file_path in files:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        chunks = splitter.split_text(code)
        await vectorise(chunks)
        typer.echo(f"Processed {file_path} ({len(chunks)} chunks)")


if __name__ == "__main__":
    app()

# VectorCode Chunker

This tool chunks source code files using [LangChain's RecursiveCharacterTextSplitter](https://python.langchain.com/docs/modules/data_connection/document_transformers/recursive_text_splitter) and stores the resulting chunks in a [ChromaDB](https://www.trychroma.com/) vector database, including line range metadata for each chunk.

## Features

- Supports chunking of code files in any language supported by LangChain.
- Stores chunks with path and line range metadata for advanced querying.
- Asynchronous, batched insertion into ChromaDB for performance.
- Command-line interface using [Typer](https://typer.tiangolo.com/).
- Progress and status logging.

## Installation

### Using [uv](https://github.com/astral-sh/uv)

1. Install [uv](https://github.com/astral-sh/uv) if you don't have it:

   ```sh
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Create a virtual environment and install dependencies:

   ```sh
   uv venv .venv
   source .venv/bin/activate
   uv sync
   ```

### Using [pipx](https://pypa.github.io/pipx/)

1. Install [pipx](https://pypa.github.io/pipx/):

   ```sh
   python -m pip install --user pipx
   ```

2. Install this project (from a local directory):

   ```sh
   pipx install --editable .
   ```

## Usage

```sh
python chunker.py chunk-and-vectorise "*.py" --language python
```

- `pattern`: Glob pattern for files to process (e.g., `"*.py"`, `"src/**/*.js"`)
- `--language`: Programming language for splitting (default: `python`). Must be supported by LangChain's `Language` enum.

Example for JavaScript files:

```sh
python chunker.py chunk-and-vectorise "src/**/*.js" --language javascript
```

## Usage (Installed CLI)

If you have installed this project using `pipx` or `pip install`, the `chunker` command will be available on your PATH.

You can use it as follows:

```sh
chunker chunk-and-vectorise "<pattern>" --language <language>
```

- `<pattern>`: Glob pattern for files to process (e.g., `"*.py"`, `"src/**/*.js"`)
- `--language <language>`: Programming language for splitting (default: `python`). Must be supported by LangChain's `Language` enum.

**Examples:**

Chunk all Python files in the current directory:
```sh
chunker chunk-and-vectorise "*.py"
```

Chunk all JavaScript files in a subdirectory:
```sh
chunker chunk-and-vectorise "src/**/*.js" --language javascript
```

If installed with pipx, you can run the CLI directly:

```sh
chunker chunk-and-vectorise "*.py" --language python
```

## Querying

After vectorising your files, you can query your ChromaDB collection for relevant code chunks using the `vectorcode` CLI.

To search for code chunks matching an expression and include chunk metadata (such as file path and line range), use:

```sh
vectorcode query "some expression" --include chunk
```

- `"some expression"`: The text or code you want to search for.
- `--include chunk`: Ensures the output includes chunk metadata (file path, start, and end lines).

**Example:**

```sh
vectorcode query "def my_function" --include chunk
```

This will return all code chunks containing `def my_function`, along with their file path and line range.

## Output

Chunks are stored in your configured ChromaDB collection, with metadata including:
- `path`: Full path to the source file
- `start`: Start line number (0-based)
- `end`: End line number (0-based)

## License

See [LICENSE](LICENSE).

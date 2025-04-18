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

## Setting up ChromaDB with Docker

You can run a ChromaDB server using Docker. The following command will start ChromaDB listening on port 8000:

```sh
docker run -d --name chromadb -p 8000:8000 chromadb/chroma
```

- This will pull the latest ChromaDB image and run it in detached mode.
- The server will be accessible at `http://localhost:8000`.

If you want to persist data between restarts, you can mount a local directory:

```sh
docker run -d --name chromadb -p 8000:8000 -v $(pwd)/chroma-data:/chroma/.chroma chromadb/chroma
```

- This will store ChromaDB data in the `chroma-data` directory in your current folder.

**Stopping and removing the container:**

```sh
docker stop chromadb
docker rm chromadb
```

For more information, see the [ChromaDB Docker documentation](https://docs.trychroma.com/deployment/docker).

## Usage

```sh
python chunker.py chunk-and-vectorise <project_dir> "<pattern>" --language <language>
```

- `<project_dir>`: Root directory of the project to search for files (e.g., `.` or `src`)
- `<pattern>`: Glob pattern for files to process (e.g., `"*.py"`, `"src/**/*.js"`)
- `--language <language>`: Programming language for splitting (default: `python`). Must be supported by LangChain's `Language` enum.

Example for JavaScript files:

```sh
python chunker.py chunk-and-vectorise src "src/**/*.js" --language javascript
```

## Using the VectorCode CLI Proxy

You can access the full `vectorcode` CLI through this tool using the `vectorcode-cli` command. This forwards all arguments to the underlying `vectorcode` command-line interface.

**Example:**

```sh
python chunker.py vectorcode-cli query "this is a query"
```

All arguments after `vectorcode-cli` are passed directly to `vectorcode`. For example, to check the version:

```sh
python chunker.py vectorcode-cli version
```

Or to run any other `vectorcode` subcommand:

```sh
python chunker.py vectorcode-cli <subcommand> [options...]
```

## Using the VectorCode MCP CLI Proxy

You can access the `vectorcode` MCP (Multi-Collection Processor) CLI through this tool using the `vectorcode-mcp` command. This forwards all arguments to the underlying `vectorcode.mcp_main` command-line interface.

**Example:**

```sh
python chunker.py vectorcode-mcp --option value
```

All arguments after `vectorcode-mcp` are passed directly to the `vectorcode.mcp_main` CLI. For example, to see available options:

```sh
python chunker.py vectorcode-mcp --help
```

## Using the Chunker MCP

You can use the MCP (Multi-Collection Processor) interface for chunking and vectorising via `chunker_mcp.py`.  
This requires you to specify the project directory with `--project_dir`.

**Example:**

```sh
python chunker_mcp.py --project_dir .  # Add other MCP options as needed
```

When using the MCP tool, the `chunk_and_vectorise` tool will use the `PROJECT_DIR` environment variable set by the `--project_dir` argument.

## Using the VectorCode LSP CLI Proxy

You can access the `vectorcode` LSP (Language Server Protocol) CLI through this tool using the `vectorcode-lsp` command. This forwards all arguments to the underlying `vectorcode.lsp_main` command-line interface.

**Example:**

```sh
python chunker.py vectorcode-lsp --option value
```

All arguments after `vectorcode-lsp` are passed directly to the `vectorcode.lsp_main` CLI. For example, to see available options:

```sh
python chunker.py vectorcode-lsp --help
```

## Usage (Installed CLI)

If you have installed this project using `pipx` or `pip install`, the `chunker` command will be available on your PATH.

You can use it as follows:

```sh
chunker chunk-and-vectorise <project_dir> "<pattern>" --language <language>
```

- `<project_dir>`: Root directory of the project to search for files (e.g., `.` or `src`)
- `<pattern>`: Glob pattern for files to process (e.g., `"*.py"`, `"src/**/*.js"`)
- `--language <language>`: Programming language for splitting (default: `python`). Must be supported by LangChain's `Language` enum.

**Examples:**

Chunk all Python files in the current directory:
```sh
chunker chunk-and-vectorise . "*.py"
```

Chunk all JavaScript files in a subdirectory:
```sh
chunker chunk-and-vectorise src "src/**/*.js" --language javascript
```

You can also use the `vectorcode-mcp` subcommand in the same way:

```sh
chunker vectorcode-mcp [options...]
```

You can also use the `vectorcode-lsp` subcommand in the same way:

```sh
chunker vectorcode-lsp [options...]
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

# VectorCode Chunker
## Table of Contents                                                                                                      
- [Features](#features)  
- [Installation](#installation)                                                                                           
  - [Using uv](#using-uv)                                                                                                 
  - [Using pipx](#using-pipx)                                                                                             
- [Setting up ChromaDB with Docker](#setting-up-chromadb-with-docker)                                                     
- [Usage](#usage)                                                                                                         
- [Using the VectorCode CLI Proxy](#using-the-vectorcode-cli-proxy)                                                       
- [Using the VectorCode MCP CLI Proxy](#using-the-vectorcode-mcp-cli-proxy)                                               
- [Using the Chunker MCP](#using-the-chunker-mcp)                                                                         
- [Using the VectorCode LSP CLI Proxy](#using-the-vectorcode-lsp-cli-proxy)                                               
- [Usage (Installed CLI)](#usage-installed-cli)                                                                           
- [Using Chunker MCP with Claude for Desktop](#using-chunker-mcp-with-claude-for-desktop)                                 
- [Using VectorCode MCP with Claude for Desktop](#using-vectorcode-mcp-with-claude-for-desktop)                           
- [Querying](#querying)                                                                                                   
- [Output](#output)  
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

## Using Chunker MCP with Claude for Desktop

You can integrate the Chunker MCP with [Claude for Desktop](https://www.anthropic.com/claude) to enable code chunking and vectorisation directly from Claude's interface. The recommended way is to install the tool globally using `pipx` and configure Claude for Desktop to use the MCP protocol.

### 1. Install Chunker Globally with pipx

First, ensure you have [pipx](https://pypa.github.io/pipx/) installed:

```sh
python -m pip install --user pipx
pipx ensurepath
```

Then, install your chunker project globally (from your project directory):

```sh
pipx install --editable .
```

This will make the `chunker` command available globally.

### 2. Configure Claude for Desktop to Use the MCP Server

Claude for Desktop supports the `{"mcpServers":{}}` protocol for tool integration.  
Add the following to your Claude for Desktop configuration (or use the UI to add a new MCP server):

```json
{
  "mcpServers": {
    "chunker": {
      "command": "chunker",
      "args": [
        "chunk-and-vectorise-mcp",
        "--project_dir",
        "/path/to/your/project"
      ]
    }
  }
}
```

- Replace `/path/to/your/project` with the absolute path to your codebase.
- The `chunker` command is provided globally by `pipx`.
- The `args` array specifies the subcommand and required arguments.

### 3. Use the Tool in Claude

Once configured, you can invoke the chunker MCP tool from Claude for Desktop.  
Use the prompts and commands as described in the "Using the Chunker MCP" section above.

---

## Using VectorCode MCP with Claude for Desktop

You can also use the VectorCode MCP (Multi-Collection Processor) via the `vectorcode_mcp` proxy command with Claude for Desktop. This allows you to access all MCP features of VectorCode from Claude's interface.

### 1. Install Chunker (and VectorCode) Globally with pipx

If you haven't already, install your chunker project globally:

```sh
pipx install --editable .
```

This will make the `chunker` command available globally, including the `vectorcode_mcp` proxy.

### 2. Configure Claude for Desktop to Use the VectorCode MCP Server

Add the following to your Claude for Desktop configuration (or use the UI to add a new MCP server):

```json
{
  "mcpServers": {
    "vectorcode": {
      "command": "chunker",
      "args": [
        "vectorcode-mcp"
      ]
    }
  }
}
```

- The `chunker` command is provided globally by `pipx`.
- The `args` array specifies the `vectorcode-mcp` subcommand, which proxies to the VectorCode MCP.

### 3. Use the Tool in Claude

Once configured, you can invoke the VectorCode MCP tool from Claude for Desktop.  
Use the prompts and commands as described in the VectorCode documentation.

---

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

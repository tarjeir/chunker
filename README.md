# VectorCode Chunker

This tool chunks source code files using [LangChain's RecursiveCharacterTextSplitter](https://python.langchain.com/docs/modules/data_connection/document_transformers/recursive_text_splitter) and stores the resulting chunks in a [ChromaDB](https://www.trychroma.com/) vector database, including line range metadata for each chunk.

## Features

- Supports chunking of code files in any language supported by LangChain.
- Stores chunks with path and line range metadata for advanced querying.
- Asynchronous, batched insertion into ChromaDB for performance.
- Command-line interface using [Typer](https://typer.tiangolo.com/).
- Progress and status logging.

## Installation

1. Clone this repository.
2. Install dependencies (example using pip):

   ```sh
   pip install -r requirements.txt
   ```

   Make sure you have the following packages (and their dependencies) installed:
   - `typer`
   - `langchain-text-splitters`
   - `chromadb`
   - `tqdm` (if you want progress bars)
   - Any dependencies required by your `vectorcode` package

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

## Output

Chunks are stored in your configured ChromaDB collection, with metadata including:
- `path`: Full path to the source file
- `start`: Start line number (0-based)
- `end`: End line number (0-based)

## License

See [LICENSE](LICENSE).

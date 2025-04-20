import tempfile
import shutil
from pathlib import Path
import pytest
from chunker_src.chunker_mcp import _parse_gitignore, _traverse_project_dir_and_ignore_dirs

def test_parse_gitignore(tmp_path):
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text(".venv/\nfoo/\nbar\n")
    spec = _parse_gitignore(tmp_path)
    assert spec is not None
    assert spec.match_file(".venv/") or spec.match_file(".venv")
    assert spec.match_file("foo/") or spec.match_file("foo")
    assert spec.match_file("bar") or spec.match_file("bar/")

def test_traverse_project_dir_and_ignore_dirs(tmp_path):
    # Setup directories
    (tmp_path / ".venv").mkdir()
    (tmp_path / "foo").mkdir()
    (tmp_path / "bar").mkdir()
    (tmp_path / "baz").mkdir()
    (tmp_path / ".git").mkdir()
    (tmp_path / "baz" / "subdir").mkdir(parents=True)
    (tmp_path / ".gitignore").write_text(".venv/\nfoo/\nbar\n")
    spec = _parse_gitignore(tmp_path)
    # Non-recursive
    dirs = _traverse_project_dir_and_ignore_dirs(tmp_path, spec, recursive=False)
    dirnames = {str(d) for d in dirs}
    assert "baz" in dirnames
    assert ".venv" not in dirnames
    assert "foo" not in dirnames
    assert "bar" not in dirnames
    assert ".git" not in dirnames
    # Recursive
    dirs = _traverse_project_dir_and_ignore_dirs(tmp_path, spec, recursive=True)
    dirnames = {str(d) for d in dirs}
    assert "baz" in dirnames
    assert "baz/subdir" in dirnames
    assert ".venv" not in dirnames
    assert "foo" not in dirnames
    assert "bar" not in dirnames
    assert ".git" not in dirnames

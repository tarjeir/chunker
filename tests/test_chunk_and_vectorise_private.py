import pytest

from chunker_src.chunk_and_vectorise import (
    _validate_glob_pattern,
    _filter_files_with_gitignore,
    _check_files_within_project_dir,
)


@pytest.mark.parametrize(
    "pattern,expected",
    [
        ("*.py", None),
        ("src/*.py", None),
        ("../*.py", ValueError),
        ("**", ValueError),
        ("**/*.py", ValueError),
        ("**/foo.py", ValueError),
    ],
    ids=[
        "simple",
        "subdir",
        "parent_traversal",
        "all_recursive",
        "recursive_py",
        "recursive_file",
    ],
)
def test__validate_glob_pattern(pattern, expected):
    result = _validate_glob_pattern(pattern)
    if expected is None:
        assert result is None
    else:
        assert isinstance(result, expected)


def test__filter_files_with_gitignore(tmp_path):
    # Setup files and .gitignore
    (tmp_path / "a.py").write_text("print('a')")
    (tmp_path / "b.py").write_text("print('b')")
    (tmp_path / "c.txt").write_text("c")
    (tmp_path / ".gitignore").write_text("b.py\n*.txt\n")
    files = [tmp_path / "a.py", tmp_path / "b.py", tmp_path / "c.txt"]

    filtered = _filter_files_with_gitignore(files, tmp_path)
    filtered_names = sorted(f.name for f in filtered)
    assert filtered_names == ["a.py"]


def test__filter_files_with_gitignore_no_gitignore(tmp_path):
    (tmp_path / "a.py").write_text("print('a')")
    files = [tmp_path / "a.py"]
    filtered = _filter_files_with_gitignore(files, tmp_path)
    assert filtered == files


def test__check_files_within_project_dir_all_inside(tmp_path):
    f1 = tmp_path / "foo.py"
    f1.write_text("x")
    f2 = tmp_path / "bar.py"
    f2.write_text("y")
    result = _check_files_within_project_dir([f1, f2], tmp_path)
    assert result is None


def test__check_files_within_project_dir_outside(tmp_path, tmp_path_factory):
    f1 = tmp_path / "foo.py"
    f1.write_text("x")
    outside_dir = tmp_path_factory.mktemp("outside")
    f2 = outside_dir / "bar.py"
    f2.write_text("y")
    result = _check_files_within_project_dir([f1, f2], tmp_path)
    assert isinstance(result, ValueError)
    assert "outside the project directory" in str(result)

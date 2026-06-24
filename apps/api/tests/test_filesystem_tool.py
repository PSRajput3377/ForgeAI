"""Tests for the sandboxed FilesystemTool."""

from tools.filesystem import FilesystemTool


def test_write_then_read(tmp_path):
    fs = FilesystemTool(tmp_path)
    assert fs.run("write", "sub/file.txt", "hi").ok
    result = fs.run("read", "sub/file.txt")
    assert result.ok and result.output == "hi"


def test_list_directory(tmp_path):
    fs = FilesystemTool(tmp_path)
    fs.run("write", "a.txt", "1")
    fs.run("write", "b.txt", "2")
    result = fs.run("list", ".")
    assert result.ok
    assert set(result.data["entries"]) == {"a.txt", "b.txt"}


def test_path_escape_is_blocked(tmp_path):
    fs = FilesystemTool(tmp_path)
    result = fs.run("read", "../../etc/passwd")
    assert not result.ok
    assert "escapes project root" in result.error

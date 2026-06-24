"""FilesystemTool — sandboxed file operations confined to a workspace root.

All paths resolve relative to ``root`` and are validated to stay inside it, so
an agent can never read or write outside the project workspace (no ``../``,
no ``/etc``, no ``~/.ssh``).

Actions: read, write, create, list, exists, search, patch, delete, rename, move.
``delete``/``rename``/``move`` require the DELETE permission, which the Tool
Manager does not grant by default (see docs/security.md).
"""

from __future__ import annotations

from pathlib import Path

from tools.base import Permission, Tool, ToolErrorCode, ToolInput, ToolResult


class FilesystemTool(Tool):
    name = "filesystem"
    description = "Read, write, search, and modify files within the project workspace."

    # Actions that mutate vs. destroy, mapped to the permission they need.
    _WRITE_ACTIONS = {"write", "create", "patch"}
    _DELETE_ACTIONS = {"delete", "rename", "move"}

    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()

    def permission_for(self, action: str) -> Permission | None:
        if action in self._DELETE_ACTIONS:
            return Permission.DELETE
        if action in self._WRITE_ACTIONS:
            return Permission.WRITE
        return Permission.READ

    def _resolve(self, relative_path: str) -> Path:
        """Resolve a path and ensure it stays within the sandbox root."""
        target = (self.root / relative_path).resolve()
        if target != self.root and self.root not in target.parents:
            raise PermissionError(relative_path)
        return target

    async def execute(self, tool_input: ToolInput) -> ToolResult:
        action = tool_input.action
        args = tool_input.args
        try:
            match action:
                case "read":
                    return self._read(args["path"])
                case "write" | "create":
                    return self._write(args["path"], args.get("content", ""))
                case "patch":
                    return self._patch(args["path"], args["find"], args["replace"])
                case "list":
                    return self._list(args.get("path", "."))
                case "exists":
                    return ToolResult.ok(
                        self.name, exists=self._resolve(args["path"]).exists()
                    )
                case "search":
                    return self._search(args["query"], args.get("path", "."))
                case "delete":
                    return self._delete(args["path"])
                case "rename" | "move":
                    return self._rename(args["path"], args["to"])
                case _:
                    return self._unknown_action(action)
        except KeyError as exc:
            return ToolResult.fail(
                self.name, ToolErrorCode.INVALID_INPUT, f"Missing arg: {exc}"
            )
        except PermissionError as exc:
            return ToolResult.fail(
                self.name, ToolErrorCode.PATH_ESCAPE, f"Path escapes workspace: {exc}"
            )

    def _read(self, path: str) -> ToolResult:
        target = self._resolve(path)
        if not target.is_file():
            return ToolResult.fail(
                self.name, ToolErrorCode.FILE_NOT_FOUND, f"Not a file: {path}"
            )
        return ToolResult.ok(self.name, output=target.read_text(encoding="utf-8"))

    def _write(self, path: str, content: str) -> ToolResult:
        target = self._resolve(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return ToolResult.ok(self.name, bytes=len(content.encode("utf-8")))

    def _patch(self, path: str, find: str, replace: str) -> ToolResult:
        target = self._resolve(path)
        if not target.is_file():
            return ToolResult.fail(
                self.name, ToolErrorCode.FILE_NOT_FOUND, f"Not a file: {path}"
            )
        text = target.read_text(encoding="utf-8")
        if find not in text:
            return ToolResult.fail(
                self.name, ToolErrorCode.INVALID_INPUT, "find text not present"
            )
        target.write_text(text.replace(find, replace), encoding="utf-8")
        return ToolResult.ok(self.name, replacements=text.count(find))

    def _list(self, path: str) -> ToolResult:
        target = self._resolve(path)
        if not target.is_dir():
            return ToolResult.fail(
                self.name, ToolErrorCode.NOT_FOUND, f"Not a directory: {path}"
            )
        entries = sorted(p.relative_to(self.root).as_posix() for p in target.iterdir())
        return ToolResult.ok(self.name, entries=entries)

    def _search(self, query: str, path: str) -> ToolResult:
        base = self._resolve(path)
        hits: list[str] = []
        for p in base.rglob("*"):
            if p.is_file():
                try:
                    if query in p.read_text(encoding="utf-8"):
                        hits.append(p.relative_to(self.root).as_posix())
                except (UnicodeDecodeError, OSError):
                    continue
        return ToolResult.ok(self.name, matches=sorted(hits))

    def _delete(self, path: str) -> ToolResult:
        target = self._resolve(path)
        if not target.exists():
            return ToolResult.fail(
                self.name, ToolErrorCode.FILE_NOT_FOUND, f"Does not exist: {path}"
            )
        if target.is_file():
            target.unlink()
        else:
            return ToolResult.fail(
                self.name, ToolErrorCode.INVALID_INPUT, "Refusing to delete a directory"
            )
        return ToolResult.ok(self.name)

    def _rename(self, path: str, to: str) -> ToolResult:
        src = self._resolve(path)
        dst = self._resolve(to)
        if not src.exists():
            return ToolResult.fail(
                self.name, ToolErrorCode.FILE_NOT_FOUND, f"Does not exist: {path}"
            )
        dst.parent.mkdir(parents=True, exist_ok=True)
        src.rename(dst)
        return ToolResult.ok(self.name, to=to)

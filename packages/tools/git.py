"""GitTool — version-control operations within the workspace repo.

Read actions (status, diff, log, branch list) require READ. ``commit`` requires
COMMIT; ``push`` requires PUSH (not granted by default). Runs the git CLI with
``cwd`` confined to the workspace root.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from tools.base import Permission, Tool, ToolError, ToolErrorCode, ToolInput, ToolResult

_READ_ACTIONS = {"status", "diff", "log", "branch", "current_branch"}


class GitTool(Tool):
    name = "git"
    description = "Run git operations (status, diff, branch, add, commit, push, ...)."

    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()

    def permission_for(self, action: str) -> Permission | None:
        if action == "push":
            return Permission.PUSH
        if action in {"commit", "add", "checkout", "branch_create", "stash", "restore"}:
            return Permission.COMMIT
        return Permission.READ

    async def _git(self, *args: str) -> tuple[int, str, str]:
        proc = await asyncio.create_subprocess_exec(
            "git",
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(self.root),
        )
        out, err = await proc.communicate()
        return (
            proc.returncode or 0,
            out.decode(errors="replace"),
            err.decode(errors="replace"),
        )

    async def execute(self, tool_input: ToolInput) -> ToolResult:
        action = tool_input.action
        args = tool_input.args

        argv: list[str]
        match action:
            case "status":
                argv = ["status", "--short"]
            case "diff":
                argv = ["diff"] + (["--cached"] if args.get("staged") else [])
            case "log":
                argv = ["log", "--oneline", "-n", str(args.get("n", 10))]
            case "current_branch":
                argv = ["rev-parse", "--abbrev-ref", "HEAD"]
            case "branch":
                argv = ["branch", "--list"]
            case "branch_create":
                argv = ["checkout", "-b", args["name"]]
            case "checkout":
                argv = ["checkout", args["ref"]]
            case "add":
                argv = ["add"] + args.get("paths", ["."])
            case "commit":
                argv = ["commit", "-m", args["message"]]
            case "stash":
                argv = ["stash"]
            case "restore":
                argv = ["restore"] + args.get("paths", ["."])
            case "push":
                argv = ["push"]
            case _:
                return self._unknown_action(action)

        try:
            code, out, err = await self._git(*argv)
        except KeyError as exc:
            return ToolResult.fail(self.name, ToolErrorCode.INVALID_INPUT, f"Missing arg: {exc}")

        if code != 0:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output=out,
                error=ToolError(
                    code=ToolErrorCode.EXECUTION_FAILED,
                    message=err.strip() or f"git {action} failed",
                ),
                metadata={"exit_code": code},
            )
        return ToolResult.ok(self.name, output=out.strip(), exit_code=code)

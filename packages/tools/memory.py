"""MemoryTool — store/retrieve/update/delete/search project memory.

Phase 3 ships an in-process key-value store keyed by memory type (conversation,
architecture, decisions, coding_style). Semantic retrieval over Qdrant is added
in the Memory + RAG phase; thanks to the capability system, agents that request
RECALL_MEMORY won't change when the backend does.
"""

from __future__ import annotations

from tools.base import Permission, Tool, ToolErrorCode, ToolInput, ToolResult

MEMORY_TYPES = {"conversation", "architecture", "decisions", "coding_style"}


class MemoryTool(Tool):
    name = "memory"
    description = "Store and retrieve project memory (conversation, decisions, style)."

    def __init__(self) -> None:
        # type -> key -> value
        self._store: dict[str, dict[str, str]] = {t: {} for t in MEMORY_TYPES}

    def permission_for(self, action: str) -> Permission | None:
        if action in {"store", "update"}:
            return Permission.WRITE
        if action == "delete":
            return Permission.DELETE
        return Permission.READ

    def _bucket(self, mtype: str) -> dict[str, str]:
        return self._store.setdefault(mtype, {})

    async def execute(self, tool_input: ToolInput) -> ToolResult:
        action = tool_input.action
        args = tool_input.args
        try:
            match action:
                case "store" | "update":
                    self._bucket(args.get("type", "conversation"))[args["key"]] = args[
                        "value"
                    ]
                    return ToolResult.ok(self.name)
                case "retrieve":
                    val = self._bucket(args.get("type", "conversation")).get(
                        args["key"]
                    )
                    if val is None:
                        return ToolResult.fail(
                            self.name,
                            ToolErrorCode.NOT_FOUND,
                            f"No memory: {args['key']}",
                        )
                    return ToolResult.ok(self.name, output=val)
                case "delete":
                    self._bucket(args.get("type", "conversation")).pop(
                        args["key"], None
                    )
                    return ToolResult.ok(self.name)
                case "search":
                    return self._search(args["query"], args.get("type"))
                case _:
                    return self._unknown_action(action)
        except KeyError as exc:
            return ToolResult.fail(
                self.name, ToolErrorCode.INVALID_INPUT, f"Missing arg: {exc}"
            )

    def _search(self, query: str, mtype: str | None) -> ToolResult:
        types = [mtype] if mtype else list(self._store)
        hits = []
        for t in types:
            for key, value in self._bucket(t).items():
                if query.lower() in key.lower() or query.lower() in value.lower():
                    hits.append({"type": t, "key": key, "value": value})
        return ToolResult.ok(self.name, output=f"{len(hits)} match(es)", matches=hits)

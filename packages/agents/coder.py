"""CoderAgent — the engineer. Writes code from task + context. Never guesses.

With a real model provider the Coder emits a complete multi-file project: it
asks for a JSON map of ``path -> file contents`` and writes every file into
``state.generated_code``, so a request like "build a todo app" produces an
actual runnable app in the PR.

With the offline ``EchoProvider`` the structured request can't be parsed, so the
Coder falls back to the original Phase-2 placeholder (a single
``generated/output.txt``) — keeping the deterministic offline workflow and its
tests unchanged (ADR-0003).
"""

from __future__ import annotations

from core.messages import AgentMessage, MessageStatus
from core.roles import AgentRole
from core.state import ProjectState

from agents.base import BaseAgent

# Cap how much we keep from any single generated file, as a guardrail against a
# runaway response. Generous enough for real source files.
_MAX_FILE_CHARS = 200_000
# Cap the number of files in one pass so a single run stays reviewable.
_MAX_FILES = 60


class CoderAgent(BaseAgent):
    role = AgentRole.CODER

    async def run(self, state: ProjectState) -> ProjectState:
        task = state.current_task
        title = task.title if task else state.user_request
        context = "\n".join(state.retrieved_docs)
        feedback = (
            f"\n\nA previous attempt was rejected. Apply this fix:\n{state.review_feedback}"
            if state.review_feedback
            else ""
        )

        files = await self._generate_files(state.user_request, title, context, feedback)

        if files:
            # Real generation: replace prior output with the fresh file set so a
            # retry fully supersedes the previous attempt.
            state.generated_code = files
        else:
            # Offline / unparseable response: original placeholder behavior.
            code = await self._ask(f"Task: {title}\nContext:\n{context}\nWrite the code.")
            state.generated_code["generated/output.txt"] = code
            if state.review_feedback:
                state.generated_code[
                    "generated/output.txt"
                ] += f"\n# applied: {state.review_feedback}"

        task_id = task.task_id if task else "n/a"
        state.record(
            AgentMessage(
                task_id=task_id,
                sender=self.role,
                status=MessageStatus.COMPLETED,
                summary=f"Generated {len(state.generated_code)} file(s)",
                files_changed=list(state.generated_code.keys()),
            )
        )
        return state

    async def _generate_files(
        self, request: str, title: str, context: str, feedback: str
    ) -> dict[str, str]:
        """Ask the model for a full project as a path->content JSON map.

        Returns a sanitized ``{path: content}`` dict, or an empty dict when the
        response isn't usable (e.g. the offline EchoProvider).
        """
        prompt = (
            "You are building a complete, runnable project that satisfies the "
            "request below. Produce EVERY file needed to run it — source code, "
            "entry point, dependency manifest (e.g. requirements.txt or "
            "package.json), a README with run instructions, and at least one "
            "test file.\n\n"
            "Respond with a single JSON object of this exact shape:\n"
            '{"files": [{"path": "relative/path.ext", "content": "<full file contents>"}]}\n'
            "Rules: paths are relative (no leading slash, no ..), content is the "
            "complete file as a string, no commentary outside the JSON.\n\n"
            f"Request:\n{request}\n\nCurrent task: {title}\n"
            f"Relevant context:\n{context or '(none)'}{feedback}"
        )
        parsed = await self._ask_json(prompt, temperature=0.2)
        return self._files_from_response(parsed)

    @staticmethod
    def _files_from_response(parsed) -> dict[str, str]:
        """Normalize a parsed model response into a safe {path: content} map."""
        if not isinstance(parsed, dict):
            return {}
        entries = parsed.get("files")
        files: dict[str, str] = {}

        def add(path, content) -> None:
            if not isinstance(path, str) or not isinstance(content, str):
                return
            safe = CoderAgent._safe_path(path)
            if safe is None:
                return
            files[safe] = content[:_MAX_FILE_CHARS]

        if isinstance(entries, list):
            for item in entries:
                if isinstance(item, dict):
                    add(item.get("path"), item.get("content"))
        elif isinstance(entries, dict):
            # Tolerate {"files": {"path": "content", ...}}.
            for path, content in entries.items():
                add(path, content)
        else:
            # Tolerate a bare {"path": "content"} map at the top level.
            for path, content in parsed.items():
                add(path, content)

        return dict(list(files.items())[:_MAX_FILES])

    @staticmethod
    def _safe_path(path: str) -> str | None:
        """Reject absolute paths and traversal; normalize separators."""
        path = path.strip().lstrip("/")
        if not path or ".." in path.split("/"):
            return None
        return path

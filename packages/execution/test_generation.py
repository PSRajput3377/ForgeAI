"""Test generation — the Testing agent can scaffold tests for new code.

Phase 5 ships deterministic scaffolding (a sensible test stub per framework) so
the loop is testable offline; the Coder/Testing agents fill in real assertions
using the LLM. The scaffold gives the execution loop something to run.
"""

from __future__ import annotations


def scaffold_python_test(target: str, func: str = "endpoint") -> str:
    """Return a minimal pytest stub for a Python target."""
    return (
        f'"""Auto-generated test scaffold for {target}."""\n\n'
        f"def test_{func}():\n"
        f"    # TODO: arrange / act / assert for {func}\n"
        f"    assert True\n"
    )


def scaffold_js_test(target: str, name: str = "feature") -> str:
    """Return a minimal vitest/jest stub for a JS/TS target."""
    return (
        f"// Auto-generated test scaffold for {target}\n"
        f'describe("{name}", () => {{\n'
        f'  it("works", () => {{\n'
        f"    expect(true).toBe(true);\n"
        f"  }});\n"
        f"}});\n"
    )


def scaffold_for(language: str, target: str) -> str:
    """Pick a scaffold by language."""
    if language in {"python"}:
        return scaffold_python_test(target)
    if language in {"javascript", "typescript"}:
        return scaffold_js_test(target)
    return f"# No scaffold available for language: {language}\n"

"""Generate ForgeAI-UseCases.pdf — complex, end-to-end worked examples.

Run:  uv run --with reportlab python scripts/make_examples_pdf.py
Output: ForgeAI-UseCases.pdf in the repo root.
"""

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

# ---- palette ---------------------------------------------------------------
INK = HexColor("#1A1F2B")
MUTE = HexColor("#5A6675")
ACCENT = HexColor("#2C6FD6")
GREEN = HexColor("#1F8A4C")
PANEL = HexColor("#F1F4F9")
BORDER = HexColor("#D5DCE6")
CODEBG = HexColor("#0F1420")
CODEINK = HexColor("#D7E0EE")

ss = getSampleStyleSheet()


def st(name, **kw):
    base = dict(fontName="Helvetica", textColor=INK, leading=14, spaceAfter=6)
    base.update(kw)
    return ParagraphStyle(name, parent=ss["Normal"], **base)


H1 = st("H1", fontName="Helvetica-Bold", fontSize=22, textColor=INK, leading=26, spaceAfter=4)
H2 = st("H2", fontName="Helvetica-Bold", fontSize=15, textColor=ACCENT, leading=19,
        spaceBefore=14, spaceAfter=6)
H3 = st("H3", fontName="Helvetica-Bold", fontSize=12, textColor=INK, leading=16,
        spaceBefore=8, spaceAfter=3)
BODY = st("BODY", fontSize=10.2, leading=15)
MUTED = st("MUTED", fontSize=9.5, textColor=MUTE, leading=13)
KICK = st("KICK", fontName="Helvetica-Bold", fontSize=9, textColor=ACCENT, leading=12,
          spaceAfter=2)
CODE = st("CODE", fontName="Courier", fontSize=8.6, textColor=CODEINK, leading=12,
          backColor=CODEBG, borderPadding=8, leftIndent=2, rightIndent=2)
BULLET = st("BULLET", fontSize=10.2, leading=15, leftIndent=12, bulletIndent=2)


def bullets(items):
    out = []
    for it in items:
        out.append(Paragraph(f"<font color='#2C6FD6'><b>&#9656;</b></font>&nbsp; {it}", BULLET))
    return out


def code(lines):
    txt = "<br/>".join(
        ln.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace(" ", "&nbsp;")
        for ln in lines
    )
    return Paragraph(txt, CODE)


def panel(flowable_text_lines, title=None):
    """A soft callout panel built as a 1-cell table."""
    inner = []
    if title:
        inner.append(Paragraph(title, H3))
    for ln in flowable_text_lines:
        inner.append(Paragraph(ln, BODY))
    t = Table([[inner]], colWidths=[170 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PANEL),
        ("BOX", (0, 0), (-1, -1), 0.6, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


def steptable(rows):
    """Stage | What happens | What you see."""
    data = [[Paragraph("<b>Agent / stage</b>", st("th", fontSize=9, textColor=HexColor("#FFFFFF"), fontName="Helvetica-Bold")),
             Paragraph("<b>What happens</b>", st("th2", fontSize=9, textColor=HexColor("#FFFFFF"), fontName="Helvetica-Bold")),
             Paragraph("<b>Output / signal</b>", st("th3", fontSize=9, textColor=HexColor("#FFFFFF"), fontName="Helvetica-Bold"))]]
    for a, b, c in rows:
        data.append([
            Paragraph(a, st("c1", fontSize=9, fontName="Helvetica-Bold", leading=12)),
            Paragraph(b, st("c2", fontSize=9, leading=12)),
            Paragraph(c, st("c3", fontSize=9, textColor=MUTE, leading=12)),
        ])
    t = Table(data, colWidths=[30 * mm, 85 * mm, 55 * mm], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#FFFFFF"), PANEL]),
        ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


# ---- page furniture --------------------------------------------------------
def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MUTE)
    canvas.drawString(20 * mm, 12 * mm, "ForgeAI — Use Cases & End-to-End Walkthroughs")
    canvas.drawRightString(190 * mm, 12 * mm, f"{doc.page}")
    canvas.setStrokeColor(BORDER)
    canvas.line(20 * mm, 15 * mm, 190 * mm, 15 * mm)
    canvas.restoreState()


doc = BaseDocTemplate("ForgeAI-UseCases.pdf", pagesize=A4,
                      leftMargin=20 * mm, rightMargin=20 * mm,
                      topMargin=18 * mm, bottomMargin=20 * mm)
frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")
doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=footer)])

E = []  # story

# ===========================================================================
# COVER
# ===========================================================================
E.append(Spacer(1, 30 * mm))
E.append(Paragraph("ForgeAI", st("cover", fontName="Helvetica-Bold", fontSize=40, textColor=INK)))
E.append(Spacer(1, 4 * mm))
E.append(Paragraph("Use Cases &amp; End-to-End Walkthroughs", st("sub", fontSize=16, textColor=MUTE)))
E.append(Spacer(1, 8 * mm))
E.append(Paragraph(
    "Four realistic, complex scenarios showing exactly how a natural-language request "
    "flows through ForgeAI's multi-agent pipeline — and how the self-improving layer "
    "turns each run into measurable, compounding value.", BODY))
E.append(Spacer(1, 6 * mm))
E.append(panel([
    "<b>1.</b>&nbsp; Add JWT authentication to a backend API",
    "<b>2.</b>&nbsp; Fix a failing CI build (self-correction + failure memory)",
    "<b>3.</b>&nbsp; Build a CRUD REST API for a startup (debate + dynamic selection)",
    "<b>4.</b>&nbsp; A team that gets better over 100 runs (the compounding loop)",
], title="What's inside"))
E.append(Spacer(1, 6 * mm))
E.append(Paragraph("12 phases · 310 tests · runs fully offline · local models, no API keys", MUTED))
E.append(PageBreak())

# ===========================================================================
# PRIMER
# ===========================================================================
E.append(Paragraph("How a request flows (the model behind every example)", H1))
E.append(Paragraph(
    "You submit one natural-language request. A <b>Manager</b> classifies and delegates it; "
    "an explicit workflow graph then sequences the specialists. Every agent reads from and "
    "writes to one shared <i>ProjectState</i> — agents never call each other directly.", BODY))
E.append(Spacer(1, 3 * mm))
E.append(code([
    "START -> manager(intake) -> planner -> research -> memory -> coder",
    "      -> execute(sandbox) -> tests -> review -> [approved?]",
    "                                         | no  -> reflection -> coder   (retry)",
    "                                         | yes -> git(propose PR) -> final -> END",
]))
E.append(Spacer(1, 4 * mm))
E.append(Paragraph("And then — the part most tools skip:", H3))
E.append(Paragraph(
    "When the run finishes, the <b>Evaluation Engine</b> scores it (outcome + cost + which "
    "prompt versions were used), stores it in the <b>Performance Database</b>, and updates the "
    "<b>Analytics</b> dashboard. Failures are remembered. Benchmarks track each release. "
    "That is what lets ForgeAI improve across runs without code changes.", BODY))
E.append(PageBreak())

# ===========================================================================
# EXAMPLE 1 — JWT AUTH
# ===========================================================================
E.append(Paragraph("EXAMPLE 1", KICK))
E.append(Paragraph("Add JWT authentication to a backend API", H1))
E.append(Paragraph("<b>Who:</b> a developer with a FastAPI app and no auth yet. "
                   "<b>Goal:</b> protected routes with login/signup, reviewed and on a PR.", MUTED))

E.append(Paragraph("The request", H2))
E.append(code(['POST /agents/run',
               '{ "user_request": "Add JWT authentication", "project_id": "auth-1" }']))

E.append(Paragraph("What happens, stage by stage", H2))
E.append(steptable([
    ("Manager", "Reads the request; <b>Dynamic Selection</b> classifies it as a <b>backend</b> task "
                "(matched signals: <i>auth, jwt, api</i>) and records the rationale.",
     "task_type = backend"),
    ("Planner", "Breaks it into ordered tasks: add dependency, hash passwords, issue/verify tokens, "
                "protect routes, register/login endpoints, tests.", "6 tasks"),
    ("Researcher", "Pulls only the relevant context — existing routes, settings, the password model.",
     "scoped context"),
    ("Memory", "Recalls past decisions (e.g. 'we use argon2', 'tokens expire in 1440m') from prior runs.",
     "long-term recall"),
    ("Coder", "Writes the auth module, token utils, and the protected dependency from the given context.",
     "generated files"),
    ("Execution", "Installs deps and runs the build inside an isolated Docker sandbox.", "build logs"),
    ("Testing", "Runs the suite; reports pass/fail with evidence.", "tests passed"),
    ("Review", "Checks security, naming, structure → APPROVED, or requests changes (→ Reflection).",
     "verdict: approved"),
    ("Git", "Authors a conventional commit on a local clone and <b>proposes</b> a PR — writes nothing yet.",
     "PR proposal (gated)"),
]))
E.append(Spacer(1, 3 * mm))
E.append(Paragraph("You approve", H2))
E.append(Paragraph(
    "The proposal appears in the <b>Approval Center</b>. You review the diff and click <b>Approve</b> → "
    "the PR is created on the real repository. Nothing reached GitHub without your decision.", BODY))
E.append(Spacer(1, 2 * mm))
E.append(panel([
    "<b>What the self-improving layer recorded:</b>",
    "&#9656; an <b>Evaluation</b>: success=true, score=0.70, prompt_versions={planner: v1, coder: v1, …}",
    "&#9656; the run now counts toward per-agent stats and the backend task-type history",
    "&#9656; if the PR is later merged, that becomes a positive <i>pr_accepted</i> signal on the record",
]))
E.append(PageBreak())

# ===========================================================================
# EXAMPLE 2 — FIX FAILING CI (self-correction + failure memory)
# ===========================================================================
E.append(Paragraph("EXAMPLE 2", KICK))
E.append(Paragraph("Fix a failing CI build — self-correction + failure memory", H1))
E.append(Paragraph("<b>Who:</b> a team whose pipeline broke. <b>Goal:</b> diagnose and fix, and never "
                   "waste time re-diagnosing the same error twice.", MUTED))

E.append(Paragraph("First encounter — diagnose from scratch", H2))
E.append(steptable([
    ("Coder → Execute", "Code runs in the sandbox; the build fails: "
     "<font face='Courier'>ModuleNotFoundError: No module named 'jwt'</font>.", "exit 1"),
    ("Testing", "Tests fail because the import is missing.", "test_passed = false"),
    ("Review", "Not approved → routes to Reflection (the retry loop).", "changes requested"),
    ("Reflection", "Diagnoses the root cause and proposes a concrete fix: <i>install pyjwt</i>. "
     "<b>Stores it</b> in the Failure Knowledge Base, keyed by a normalized signature.",
     "fix proposed + stored"),
    ("Coder (retry)", "Applies the fix; Execute + Tests now pass; Review approves.", "approved"),
]))
E.append(Spacer(1, 3 * mm))
E.append(Paragraph("Next encounter — fixed instantly", H2))
E.append(Paragraph(
    "Weeks later, a different project throws the same error — buried in a long traceback. "
    "The signature normalizer collapses both to the same key, so Reflection <b>recalls the "
    "known-good fix</b> and applies it <i>without calling the model at all</i>.", BODY))
E.append(Spacer(1, 2 * mm))
E.append(code([
    "error_signature('Traceback ...\\nModuleNotFoundError: No module named \\'jwt\\'')",
    "   ->  'modulenotfounderror:jwt'      # same key as the first time",
    "recall('modulenotfounderror:jwt')",
    "   ->  fix='pip install pyjwt'  outcome=RESOLVED   # reused, no LLM call",
]))
E.append(Spacer(1, 3 * mm))
E.append(panel([
    "<b>Why this matters:</b> the system behaves like a Stack Overflow for itself. A fix that "
    "later fails is demoted, so the knowledge base self-corrects — no fix is trusted forever.",
]))
E.append(PageBreak())

# ===========================================================================
# EXAMPLE 3 — CRUD API (debate + selection)
# ===========================================================================
E.append(Paragraph("EXAMPLE 3", KICK))
E.append(Paragraph("Build a CRUD REST API — multi-agent debate in action", H1))
E.append(Paragraph("<b>Who:</b> a startup that needs an endpoint fast but done right. "
                   "<b>Goal:</b> a well-scoped plan chosen from competing approaches.", MUTED))

E.append(Paragraph("The request", H2))
E.append(code(['POST /agents/run',
               '{ "user_request": "Create a CRUD REST API for todo items",',
               '  "project_id": "todos-1" }      # workflow built with debate_planner = 3']))

E.append(Paragraph("The Planner debates instead of guessing once", H2))
E.append(Paragraph(
    "With debate enabled, <b>three independent Planner attempts</b> run from different angles — "
    "no attempt sees another's output:", BODY))
E.append(Spacer(1, 1 * mm))
E.append(steptable([
    ("Attempt 0", "<i>Simplest-increment</i> angle: ship a minimal create+list first.",
     "plan A"),
    ("Attempt 1", "<i>Risk-first</i> angle: tackle validation, pagination, and error paths early.",
     "plan B"),
    ("Attempt 2", "<i>Thorough</i> angle: cover tests, docs, and error handling explicitly.",
     "plan C"),
    ("Judge (Review)", "Scores the candidates by a documented, deterministic rubric and records "
     "<b>which won and why</b>. The winning plan drives the rest of the pipeline.",
     "winner + rationale"),
]))
E.append(Spacer(1, 3 * mm))
E.append(Paragraph("Then the normal pipeline runs on the winning plan", H2))
E.append(Paragraph(
    "Researcher → Memory → Coder → Execute → Tests → Review → Git, exactly as in Example 1 — "
    "but starting from a plan chosen out of three, which widens the solution space and reduces "
    "the chance of a weak first guess derailing the run.", BODY))
E.append(Spacer(1, 2 * mm))
E.append(panel([
    "<b>Recorded for the dashboard:</b> the debate decision (winner index + judge rationale) lives "
    "on the run's audit trail; the Evaluation captures the score so debated vs. non-debated runs "
    "can be compared over time. Debate is <b>off by default</b> and deterministic — same input, "
    "same winner — so it is safe and reproducible.",
]))
E.append(PageBreak())

# ===========================================================================
# EXAMPLE 4 — THE COMPOUNDING LOOP
# ===========================================================================
E.append(Paragraph("EXAMPLE 4", KICK))
E.append(Paragraph("A team that gets better over 100 runs", H1))
E.append(Paragraph("<b>Who:</b> any team running ForgeAI continuously. "
                   "<b>Goal:</b> improvement that compounds — without anyone editing agent code.", MUTED))

E.append(Paragraph("Run 1 vs. Run 100", H2))
E.append(steptable([
    ("Run 1", "Baseline. Scored and stored. Prompts at v1. Failures start filling the knowledge base.",
     "score recorded"),
    ("Runs 2–50", "Recurring errors are fixed instantly from memory. Each run's score + prompt "
     "version + outcome accrue in the Performance Database.", "stats accumulate"),
    ("Prompt A/B", "Someone registers Planner <b>v2</b>. Runs split across v1/v2; per-version stats "
     "are derived from the records.", "v1 vs v2 on the dashboard"),
    ("Promotion gate", "Once v2 has enough samples <i>and</i> clears the score margin, the system "
     "<b>recommends</b> promoting it — but it requires human approval; it never auto-promotes.",
     "gated recommendation"),
    ("Workflow-opt", "If a task type succeeds uniformly without a step mattering, the system "
     "<b>suggests</b> A/B-testing the pipeline without it — advisory only, the graph is never "
     "auto-edited.", "gated suggestion"),
    ("Benchmarks", "Each release runs the versioned scenario suite; the pass-rate trend shows "
     "whether the platform actually got better release over release.", "trend per version"),
]))
E.append(Spacer(1, 3 * mm))
E.append(panel([
    "<b>The compounding effect:</b> measurement (every run scored) + memory (failures reused) + "
    "comparison (versioned prompts &amp; benchmarks) + gated learning (promote/optimize on real "
    "data) means Run 100 is measurably stronger than Run 1 — and you can <i>prove</i> it on the "
    "Analytics dashboard, not just claim it.",
], title="Why 100 &gt; 1"))
E.append(Spacer(1, 4 * mm))

E.append(Paragraph("Try the whole loop yourself", H2))
E.append(code([
    "# offline, deterministic, no models needed — every Phase 12 component:",
    "cd apps/api",
    "PYTHONPATH=\"$PWD:$PWD/../../packages\" \\",
    "  uv run python ../../scripts/demo_phase12.py",
]))
E.append(Spacer(1, 3 * mm))
E.append(Paragraph(
    "All 12 phases complete · 310 tests passing · fully documented · runs on local models.",
    MUTED))

doc.build(E)
print("Saved ForgeAI-UseCases.pdf")

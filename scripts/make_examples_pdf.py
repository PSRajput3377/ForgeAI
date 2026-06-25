"""Generate ForgeAI-UseCases.pdf — a polished, end-to-end use-case booklet.

Run:  uv run --with reportlab python scripts/make_examples_pdf.py
Output: ForgeAI-UseCases.pdf in the repo root.
"""

from reportlab.lib.colors import HexColor, Color
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

# ---------------------------------------------------------------- palette ---
INK = HexColor("#11151F")
MUTE = HexColor("#5C6775")
FAINT = HexColor("#8A94A3")
ACCENT = HexColor("#2F6BEC")      # blue
ACCENT2 = HexColor("#7A5AF8")     # violet
GREEN = HexColor("#16A34A")
AMBER = HexColor("#D97706")
PANEL = HexColor("#F3F6FC")
PANEL2 = HexColor("#EBF1FE")
BORDER = HexColor("#D9E1EE")
CODEBG = HexColor("#0E1422")
CODEINK = HexColor("#CBD6E8")
CODEKEY = HexColor("#7FB0FF")
WHITE = HexColor("#FFFFFF")
NAVY = HexColor("#0B1020")

PAGE_W, PAGE_H = A4
ML = 18 * mm
CONTENT_W = PAGE_W - 2 * ML

ss = getSampleStyleSheet()


def fill_poly(c, pts):
    """Fill a polygon on a reportlab canvas (no native polygon method)."""
    p = c.beginPath()
    p.moveTo(*pts[0])
    for pt in pts[1:]:
        p.lineTo(*pt)
    p.close()
    c.drawPath(p, stroke=0, fill=1)


def style(name, **kw):
    base = dict(fontName="Helvetica", textColor=INK, leading=14, spaceAfter=6)
    base.update(kw)
    return ParagraphStyle(name, parent=ss["Normal"], **base)


BODY = style("BODY", fontSize=10.3, leading=15.5)
MUTED = style("MUTED", fontSize=9.3, textColor=MUTE, leading=13)
H2 = style("H2", fontName="Helvetica-Bold", fontSize=13.5, textColor=INK, leading=17,
           spaceBefore=12, spaceAfter=5)
H3 = style("H3", fontName="Helvetica-Bold", fontSize=11, textColor=ACCENT, leading=15,
           spaceBefore=6, spaceAfter=3)
LEAD = style("LEAD", fontSize=11, leading=16, textColor=MUTE)
CODE = style("CODE", fontName="Courier", fontSize=8.7, textColor=CODEINK, leading=13)
WHITEBODY = style("WB", fontSize=10.3, leading=15.5, textColor=WHITE)


# ----------------------------------------------------------- custom flowables
class HRule(Flowable):
    def __init__(self, width, color=BORDER, thick=0.6, pad=0):
        super().__init__()
        self.width, self.color, self.thick, self.pad = width, color, thick, pad

    def wrap(self, *a):
        return self.width, self.thick + 2 * self.pad

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thick)
        self.canv.line(0, self.pad, self.width, self.pad)


class Banner(Flowable):
    """A section banner: number badge + kicker + title on a soft bar."""

    def __init__(self, num, kicker, title, w=CONTENT_W, accent=ACCENT):
        super().__init__()
        self.num, self.kicker, self.title, self.w, self.accent = num, kicker, title, w, accent
        self.h = 20 * mm

    def wrap(self, *a):
        return self.w, self.h

    def draw(self):
        c = self.canv
        # soft panel
        c.setFillColor(PANEL)
        c.roundRect(0, 0, self.w, self.h, 3 * mm, stroke=0, fill=1)
        # accent left bar
        c.setFillColor(self.accent)
        c.roundRect(0, 0, 3.2 * mm, self.h, 1.6 * mm, stroke=0, fill=1)
        c.rect(2 * mm, 0, 1.5 * mm, self.h, stroke=0, fill=1)
        # number badge
        bs = 13 * mm
        bx, by = 7 * mm, (self.h - bs) / 2
        c.setFillColor(self.accent)
        c.roundRect(bx, by, bs, bs, 2.5 * mm, stroke=0, fill=1)
        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 17)
        c.drawCentredString(bx + bs / 2, by + bs / 2 - 6, str(self.num))
        # text
        tx = bx + bs + 6 * mm
        c.setFillColor(self.accent)
        c.setFont("Helvetica-Bold", 8.5)
        c.drawString(tx, self.h - 7 * mm, self.kicker.upper())
        c.setFillColor(INK)
        c.setFont("Helvetica-Bold", 15.5)
        c.drawString(tx, self.h - 13.5 * mm, self.title)


class FlowDiagram(Flowable):
    """The pipeline as a row of chips with arrows, wrapping to two rows."""

    def __init__(self, stages, w=CONTENT_W):
        super().__init__()
        self.w = w
        self.rows = [stages[:5], stages[5:]]
        self.h = 26 * mm

    def wrap(self, *a):
        return self.w, self.h

    def draw(self):
        c = self.canv
        chip_w, chip_h, gap = 31 * mm, 9 * mm, 3.5 * mm
        for ri, row in enumerate(self.rows):
            y = self.h - 9 * mm - ri * 14 * mm
            x = 0
            for i, (label, kind) in enumerate(row):
                col = {"start": NAVY, "agent": ACCENT, "gate": AMBER,
                       "end": GREEN}.get(kind, ACCENT)
                c.setFillColor(col)
                c.roundRect(x, y, chip_w, chip_h, 2 * mm, stroke=0, fill=1)
                c.setFillColor(WHITE)
                c.setFont("Helvetica-Bold", 7.8)
                c.drawCentredString(x + chip_w / 2, y + chip_h / 2 - 2.6, label)
                # arrow
                if i < len(row) - 1:
                    ax = x + chip_w + 0.6 * mm
                    c.setStrokeColor(FAINT)
                    c.setLineWidth(1)
                    c.line(ax, y + chip_h / 2, ax + gap - 1.2 * mm, y + chip_h / 2)
                    c.setFillColor(FAINT)
                    fill_poly(c, [(ax + gap - 1.2 * mm, y + chip_h / 2),
                                  (ax + gap - 2.6 * mm, y + chip_h / 2 + 1.4 * mm),
                                  (ax + gap - 2.6 * mm, y + chip_h / 2 - 1.4 * mm)])
                x += chip_w + gap


def code_block(lines):
    """Dark terminal-style block with keyword tinting on the first token."""
    rendered = []
    for ln in lines:
        esc = ln.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace(" ", "&nbsp;")
        rendered.append(esc)
    body = "<br/>".join(rendered)
    p = Paragraph(body, CODE)
    t = Table([[p]], colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CODEBG),
        ("LEFTPADDING", (0, 0), (-1, -1), 11),
        ("RIGHTPADDING", (0, 0), (-1, -1), 11),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("ROUNDEDCORNERS", [4, 4, 4, 4]),
    ]))
    return t


def callout(lines, title=None, accent=ACCENT, bg=PANEL2):
    inner = []
    if title:
        inner.append(Paragraph(title, style("ct", fontName="Helvetica-Bold",
                                            fontSize=10.5, textColor=accent, spaceAfter=4)))
    for ln in lines:
        inner.append(Paragraph(ln, style("cb", fontSize=9.6, leading=14)))
    body = Table([[inner]], colWidths=[CONTENT_W - 4 * mm])
    body.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0),
                              ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                              ("TOPPADDING", (0, 0), (-1, -1), 1),
                              ("BOTTOMPADDING", (0, 0), (-1, -1), 1)]))
    outer = Table([[body]], colWidths=[CONTENT_W])
    outer.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("LINEBEFORE", (0, 0), (0, -1), 2.4, accent),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return outer


def steptable(rows):
    th = style("th", fontSize=8.6, textColor=WHITE, fontName="Helvetica-Bold", leading=11)
    head = [Paragraph("STAGE", th), Paragraph("WHAT HAPPENS", th), Paragraph("OUTPUT", th)]
    data = [head]
    for a, b, c in rows:
        data.append([
            Paragraph(a, style("c1", fontSize=8.8, fontName="Helvetica-Bold", leading=11.5)),
            Paragraph(b, style("c2", fontSize=8.8, leading=11.5)),
            Paragraph(c, style("c3", fontSize=8.5, textColor=MUTE, leading=11.5,
                               fontName="Helvetica-Oblique")),
        ])
    t = Table(data, colWidths=[26 * mm, 90 * mm, 38 * mm], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, PANEL]),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, BORDER),
        ("LINEAFTER", (0, 0), (-2, -1), 0.4, BORDER),
        ("BOX", (0, 0), (-1, -1), 0.6, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


# -------------------------------------------------------------- page canvases
def cover_page(canvas, doc):
    c = canvas
    c.saveState()
    # full navy background
    c.setFillColor(NAVY)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    # accent diagonal band
    c.setFillColor(ACCENT)
    c.setFillAlpha(0.16)
    fill_poly(c, [(0, PAGE_H), (PAGE_W, PAGE_H), (PAGE_W, PAGE_H - 70 * mm), (0, PAGE_H - 40 * mm)])
    c.setFillColor(ACCENT2)
    c.setFillAlpha(0.12)
    fill_poly(c, [(0, 0), (PAGE_W, 0), (PAGE_W, 55 * mm), (0, 80 * mm)])
    c.setFillAlpha(1)
    # accent rule
    c.setStrokeColor(ACCENT)
    c.setLineWidth(3)
    c.line(ML, PAGE_H - 118 * mm, ML + 28 * mm, PAGE_H - 118 * mm)
    # wordmark
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(ML, PAGE_H - 22 * mm, "ForgeAI")
    c.setFillColor(HexColor("#9DB4E8"))
    c.setFont("Helvetica", 9)
    c.drawRightString(PAGE_W - ML, PAGE_H - 22 * mm, "Autonomous AI Engineering Platform")
    # title
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 40)
    c.drawString(ML, PAGE_H - 100 * mm, "Use Cases &")
    c.drawString(ML, PAGE_H - 116 * mm, "End-to-End Flows")
    c.setFillColor(HexColor("#AFC0E6"))
    c.setFont("Helvetica", 13)
    c.drawString(ML, PAGE_H - 130 * mm,
                 "Four complex scenarios — how one request becomes a reviewed PR,")
    c.drawString(ML, PAGE_H - 137 * mm,
                 "and how every run makes the system measurably better.")
    # stat chips
    chips = ["12 phases complete", "310 tests passing", "runs fully offline", "local models"]
    x = ML
    c.setFont("Helvetica-Bold", 8.5)
    for ch in chips:
        w = c.stringWidth(ch, "Helvetica-Bold", 8.5) + 10 * mm
        c.setFillColor(HexColor("#1A2540"))
        c.roundRect(x, 30 * mm, w, 8 * mm, 2 * mm, stroke=0, fill=1)
        c.setFillColor(HexColor("#9DB4E8"))
        c.drawString(x + 5 * mm, 32.5 * mm, ch)
        x += w + 4 * mm
    c.restoreState()


def content_page(canvas, doc):
    c = canvas
    c.saveState()
    # header strip
    c.setFillColor(NAVY)
    c.rect(0, PAGE_H - 12 * mm, PAGE_W, 12 * mm, stroke=0, fill=1)
    c.setFillColor(ACCENT)
    c.rect(0, PAGE_H - 12.8 * mm, PAGE_W, 0.8 * mm, stroke=0, fill=1)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(ML, PAGE_H - 8 * mm, "ForgeAI")
    c.setFillColor(HexColor("#9DB4E8"))
    c.setFont("Helvetica", 8)
    c.drawRightString(PAGE_W - ML, PAGE_H - 8 * mm, "Use Cases & End-to-End Flows")
    # footer
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.5)
    c.line(ML, 13 * mm, PAGE_W - ML, 13 * mm)
    c.setFillColor(FAINT)
    c.setFont("Helvetica", 8)
    c.drawString(ML, 9 * mm, "github.com/PSRajput3377/ForgeAI")
    c.drawRightString(PAGE_W - ML, 9 * mm, f"{doc.page}")
    c.restoreState()


doc = BaseDocTemplate("ForgeAI-UseCases.pdf", pagesize=A4,
                      leftMargin=ML, rightMargin=ML, topMargin=18 * mm, bottomMargin=18 * mm)
cover_frame = Frame(0, 0, PAGE_W, PAGE_H, id="cover",
                    leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
body_frame = Frame(ML, 16 * mm, CONTENT_W, PAGE_H - 34 * mm, id="body")
doc.addPageTemplates([
    PageTemplate(id="cover", frames=[cover_frame], onPage=cover_page),
    PageTemplate(id="content", frames=[body_frame], onPage=content_page),
])

E = []
E.append(NextPageTemplate("content"))
E.append(PageBreak())  # leave cover page (drawn by canvas) blank of flowables

# ============================================================= PRIMER ========
E.append(Paragraph("The model behind every example", H2))
E.append(Paragraph(
    "You submit one natural-language request. A <b>Manager</b> classifies and delegates it; an "
    "explicit workflow graph then sequences the specialists. Every agent reads from and writes to "
    "one shared <i>ProjectState</i> — they never call each other directly.", BODY))
E.append(Spacer(1, 2 * mm))
E.append(FlowDiagram([
    ("Manager", "start"), ("Planner", "agent"), ("Researcher", "agent"),
    ("Memory", "agent"), ("Coder", "agent"),
    ("Execute", "agent"), ("Tests", "agent"), ("Review", "gate"),
    ("Git / PR", "gate"), ("Final", "end"),
]))
E.append(callout([
    "When the run finishes, the <b>Evaluation Engine</b> scores it (outcome + cost + which prompt "
    "versions ran), stores it in the <b>Performance Database</b>, and updates the <b>Analytics</b> "
    "dashboard. Failures are remembered; benchmarks track each release. <b>That</b> is what lets "
    "ForgeAI improve across runs without code changes.",
], title="The part most tools skip", accent=GREEN, bg=HexColor("#EAF7EF")))
E.append(Spacer(1, 3 * mm))
E.append(Paragraph("Legend:&nbsp; "
                   "<font color='#0B1020'>&#9632;</font> start &nbsp;&nbsp;"
                   "<font color='#2F6BEC'>&#9632;</font> agent &nbsp;&nbsp;"
                   "<font color='#D97706'>&#9632;</font> gate / approval &nbsp;&nbsp;"
                   "<font color='#16A34A'>&#9632;</font> end", MUTED))
E.append(PageBreak())

# ============================================================= EXAMPLE 1 =====
E.append(Banner(1, "Backend feature", "Add JWT authentication to an API"))
E.append(Spacer(1, 3 * mm))
E.append(Paragraph("<b>Who:</b> a developer with a FastAPI app and no auth yet.&nbsp;&nbsp;"
                   "<b>Goal:</b> protected routes with login/signup — reviewed, on a PR.", LEAD))
E.append(Paragraph("The request", H3))
E.append(code_block(['POST /agents/run',
                     '{ "user_request": "Add JWT authentication", "project_id": "auth-1" }']))
E.append(Spacer(1, 3 * mm))
E.append(Paragraph("Stage by stage", H3))
E.append(steptable([
    ("Manager", "Reads the request; <b>Dynamic Selection</b> classifies it as <b>backend</b> "
                "(signals: auth, jwt, api) and records the rationale.", "task_type = backend"),
    ("Planner", "Breaks it into ordered tasks: add dep, hash passwords, issue/verify tokens, "
                "protect routes, register/login, tests.", "6 tasks"),
    ("Researcher", "Pulls only the relevant context — routes, settings, the user model.", "scoped context"),
    ("Memory", "Recalls past decisions ('we use argon2', 'tokens expire in 1440m').", "long-term recall"),
    ("Coder", "Writes the auth module, token utils, and protected dependency from context.", "generated files"),
    ("Execution", "Installs deps and builds inside an isolated Docker sandbox.", "build logs"),
    ("Testing", "Runs the suite; reports pass/fail with evidence.", "tests passed"),
    ("Review", "Checks security, naming, structure &#8594; APPROVED (else &#8594; Reflection).", "verdict: approved"),
    ("Git", "Authors a commit on a local clone and <b>proposes</b> a PR — writes nothing yet.", "PR proposal (gated)"),
]))
E.append(Spacer(1, 3 * mm))
E.append(callout([
    "&#9656;&nbsp; The proposal lands in the <b>Approval Center</b>; you review the diff and click "
    "<b>Approve</b> &#8594; the PR is created. Nothing reached GitHub without your decision.",
    "&#9656;&nbsp; Recorded: an <b>Evaluation</b> (success=true, score=0.70, prompt_versions=v1) that "
    "now counts toward per-agent stats. A later merge becomes a positive <i>pr_accepted</i> signal.",
], title="You approve — then it's measured", accent=ACCENT))
E.append(PageBreak())

# ============================================================= EXAMPLE 2 =====
E.append(Banner(2, "Self-correction", "Fix a failing CI build — and never re-diagnose it",
                accent=AMBER))
E.append(Spacer(1, 3 * mm))
E.append(Paragraph("<b>Who:</b> a team whose pipeline broke.&nbsp;&nbsp;"
                   "<b>Goal:</b> diagnose and fix — and never waste time on the same error twice.", LEAD))
E.append(Paragraph("First encounter — diagnose from scratch", H3))
E.append(steptable([
    ("Coder &#8594; Execute", "Code runs in the sandbox; build fails: "
     "ModuleNotFoundError: No module named 'jwt'.", "exit 1"),
    ("Testing", "Tests fail — the import is missing.", "test_passed = false"),
    ("Review", "Not approved &#8594; routes to Reflection (the retry loop).", "changes requested"),
    ("Reflection", "Diagnoses the root cause and proposes a fix (install pyjwt); <b>stores it</b> in "
     "the Failure KB, keyed by a normalized signature.", "fix proposed + stored"),
    ("Coder (retry)", "Applies the fix; Execute + Tests pass; Review approves.", "approved"),
]))
E.append(Spacer(1, 3 * mm))
E.append(Paragraph("Next encounter — fixed instantly, no model call", H3))
E.append(Paragraph("Weeks later a different project throws the same error, buried in a long "
                   "traceback. The signature normalizer collapses both to one key, so Reflection "
                   "<b>recalls the known-good fix</b>:", BODY))
E.append(code_block([
    "error_signature('Traceback ...\\nModuleNotFoundError: No module named \\'jwt\\'')",
    "    ->  'modulenotfounderror:jwt'        # same key as the first time",
    "recall('modulenotfounderror:jwt')",
    "    ->  fix='pip install pyjwt'  outcome=RESOLVED    # reused, zero LLM cost",
]))
E.append(Spacer(1, 3 * mm))
E.append(callout([
    "The system behaves like a <b>Stack Overflow for itself</b>. A fix that later fails is demoted, "
    "so the knowledge base self-corrects — no fix is trusted forever.",
], title="Why this matters", accent=AMBER, bg=HexColor("#FEF6E9")))
E.append(PageBreak())

# ============================================================= EXAMPLE 3 =====
E.append(Banner(3, "Multi-agent debate", "Build a CRUD REST API — three plans, one winner",
                accent=ACCENT2))
E.append(Spacer(1, 3 * mm))
E.append(Paragraph("<b>Who:</b> a startup that needs an endpoint fast but done right.&nbsp;&nbsp;"
                   "<b>Goal:</b> a well-scoped plan chosen from competing approaches.", LEAD))
E.append(code_block(['POST /agents/run',
                     '{ "user_request": "Create a CRUD REST API for todo items",',
                     '  "project_id": "todos-1" }       # built with debate_planner = 3']))
E.append(Spacer(1, 3 * mm))
E.append(Paragraph("The Planner debates instead of guessing once", H3))
E.append(Paragraph("Three <b>independent</b> attempts run from different angles — no attempt sees "
                   "another's output:", BODY))
E.append(steptable([
    ("Attempt 0", "<i>Simplest-increment</i> — ship a minimal create + list first.", "plan A"),
    ("Attempt 1", "<i>Risk-first</i> — tackle validation, pagination, error paths early.", "plan B"),
    ("Attempt 2", "<i>Thorough</i> — cover tests, docs, and error handling explicitly.", "plan C"),
    ("Judge (Review)", "Scores candidates by a documented, deterministic rubric and records "
     "<b>which won and why</b>. The winner drives the pipeline.", "winner + rationale"),
]))
E.append(Spacer(1, 3 * mm))
E.append(callout([
    "The debate decision (winner + judge rationale) is on the run's audit trail; the Evaluation "
    "captures the score, so debated vs. non-debated runs can be compared over time. Debate is "
    "<b>off by default</b> and <b>deterministic</b> — same input, same winner — so it is safe and "
    "reproducible.",
], title="Recorded for the dashboard", accent=ACCENT2, bg=HexColor("#F1EEFE")))
E.append(PageBreak())

# ============================================================= EXAMPLE 4 =====
E.append(Banner(4, "The compounding loop", "A team that gets better over 100 runs",
                accent=GREEN))
E.append(Spacer(1, 3 * mm))
E.append(Paragraph("<b>Who:</b> any team running ForgeAI continuously.&nbsp;&nbsp;"
                   "<b>Goal:</b> improvement that compounds — without anyone editing agent code.", LEAD))
E.append(steptable([
    ("Run 1", "Baseline. Scored and stored. Prompts at v1. Failures start filling the KB.", "score recorded"),
    ("Runs 2&#8211;50", "Recurring errors fixed instantly from memory; scores + versions + outcomes "
     "accrue in the Performance DB.", "stats accumulate"),
    ("Prompt A/B", "Someone registers Planner <b>v2</b>; runs split v1/v2; per-version stats are "
     "derived from the records.", "v1 vs v2 on dashboard"),
    ("Promotion gate", "Once v2 has enough samples and clears the score margin, the system "
     "<b>recommends</b> promotion — requires approval, never automatic.", "gated recommendation"),
    ("Workflow-opt", "If a task type succeeds uniformly without a step mattering, it <b>suggests</b> "
     "A/B-testing without it — advisory; the graph is never auto-edited.", "gated suggestion"),
    ("Benchmarks", "Each release runs the versioned suite; the pass-rate trend shows real "
     "improvement, release over release.", "trend per version"),
]))
E.append(Spacer(1, 3 * mm))
E.append(callout([
    "Measurement (every run scored) + memory (failures reused) + comparison (versioned prompts &amp; "
    "benchmarks) + gated learning means Run 100 is measurably stronger than Run 1 — and you can "
    "<b>prove</b> it on the Analytics dashboard, not just claim it.",
], title="Why 100 > 1", accent=GREEN, bg=HexColor("#EAF7EF")))
E.append(Spacer(1, 4 * mm))
E.append(Paragraph("Run the whole loop yourself", H3))
E.append(code_block([
    "# offline, deterministic, no models needed — every Phase 12 component:",
    "cd apps/api",
    'PYTHONPATH="$PWD:$PWD/../../packages" \\',
    "  uv run python ../../scripts/demo_phase12.py",
]))
E.append(Spacer(1, 3 * mm))
E.append(HRule(CONTENT_W))
E.append(Spacer(1, 2 * mm))
E.append(Paragraph("All 12 phases complete &#183; 310 tests passing &#183; 25 ADRs &#183; "
                   "fully documented &#183; runs on local models.", MUTED))

doc.build(E)
print("Saved ForgeAI-UseCases.pdf")

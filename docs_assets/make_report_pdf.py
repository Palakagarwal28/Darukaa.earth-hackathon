"""Build Darukaa_Earth_Solution.pdf with reportlab. Run: python docs_assets/make_report_pdf.py"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, Image, PageBreak, HRFlowable)
from reportlab.lib.enums import TA_CENTER

REPO = "https://github.com/Palakagarwal28/Darukaa.earth-hackathon"
A = "docs_assets/"
W, H = A4

doc = SimpleDocTemplate("Darukaa_Earth_Solution.pdf", pagesize=A4,
                        leftMargin=0.8 * inch, rightMargin=0.8 * inch,
                        topMargin=0.7 * inch, bottomMargin=0.7 * inch,
                        title="Darukaa.Earth — AI Biodiversity Intelligence (Hackathon Solution)",
                        author="Palak Agarwal")
ss = getSampleStyleSheet()
title = ParagraphStyle("T", parent=ss["Title"], fontSize=22, leading=26, textColor=colors.HexColor("#123324"))
h1 = ParagraphStyle("H1", parent=ss["Heading1"], fontSize=15, leading=19, textColor=colors.HexColor("#1c4630"),
                    spaceBefore=14, spaceAfter=6)
h2 = ParagraphStyle("H2", parent=ss["Heading2"], fontSize=12, leading=15, textColor=colors.HexColor("#2c7a4e"))
body = ParagraphStyle("B", parent=ss["BodyText"], fontSize=10, leading=14)
small = ParagraphStyle("S", parent=body, fontSize=9, leading=12, textColor=colors.HexColor("#444444"))
cap = ParagraphStyle("C", parent=body, fontSize=9, leading=12, alignment=TA_CENTER,
                     textColor=colors.HexColor("#555555"), spaceBefore=2, spaceAfter=8)
link = ParagraphStyle("L", parent=body, fontSize=11, leading=14, textColor=colors.HexColor("#1a5c34"))

S = []
def H(t): S.append(Paragraph(t, h1))
def P(t, style=body): S.append(Paragraph(t, style))
def B(items):
    for it in items: S.append(Paragraph("•  " + it, body))
    S.append(Spacer(1, 4))
def Tbl(rows, widths=None):
    t = Table(rows, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1c4630")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 9), ("LEADING", (0, 0), (-1, -1), 12),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#999999")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eef5ef")]),
    ]))
    S.append(t); S.append(Spacer(1, 8))
def Fig(path, width, caption):
    S.append(Image(path, width=width * inch, height=width * inch * 0.62, kind="proportional"))
    S.append(Paragraph("Figure — " + caption, cap))

S.append(Paragraph("Darukaa.Earth:<br/>AI Biodiversity Intelligence Chatbot", title))
S.append(Spacer(1, 6))
S.append(Paragraph("Hackathon solution document — an AI environmental scientist, not a chatbot.", body))
S.append(Spacer(1, 4))
S.append(Paragraph("GitHub repository: <link href='%s'>%s</link>" % (REPO, REPO), link))
P("The repository holds the complete project: backend, knowledge base, frontend, tests, CI. "
  "Runs fully offline — no deployment, credentials, or API keys required.")
S.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1c4630")))

H("1. Objective")
P("Build an AI-powered conversational system that maintains a structured knowledge base of "
  "biodiversity and environmental metrics, understands queries about ecosystems, land and climate, "
  "generates actionable non-obvious recommendations, and supports each with scientific reasoning "
  "and evidence.")

H("2. Tech stack")
Tbl([
    ["Layer", "Technology", "Why"],
    ["API backend", "FastAPI (Python) + Uvicorn", "Typed endpoints, OpenAPI docs at /docs"],
    ["Retrieval (RAG)", "BM25 + agro synonyms (default); TF-IDF / dense optional", "7/7 benchmark, offline, explainable"],
    ["Knowledge store", "Versioned JSON, 32 evidence cards + schema", "Auditable; migratable to pgvector/Chroma"],
    ["Reasoning", "Deterministic multi-metric engine", "No hallucinated advice, reproducible"],
    ["Conversation", "Slot-filling + SQLite memory", "Clarifying Qs, context awareness"],
    ["Frontend", "HTML/CSS/JS, zero build step", "3 tabs served by the same server"],
    ["Optional", "Open-Meteo (keyless) + LLM rephrase", "Graceful offline fallback"],
    ["Quality", "pytest (12 tests) + GitHub Actions", "Green on every push"],
], widths=[1.5 * inch, 2.2 * inch, 2.9 * inch])

H("3. System architecture")
Fig(A + "architecture.png", 6.2, "end-to-end architecture: deterministic engine + RAG evidence.")
Tbl([
    ["Stage", "Module", "Role"],
    ["1. Input", "Chat / Assess", "Text, structured JSON, geo lat/lon (bonus)"],
    ["2. Conversation", "src/conversation.py", "Metric extraction; clarifying Qs; SQLite memory"],
    ["3. Enrichment", "src/geo.py, integrations.py", "Region inference; optional flagged climate fill"],
    ["4. Retrieval", "src/retriever.py, bm25.py", "BM25 over 32 cards; kb_id + score + matched terms"],
    ["5. Reasoning", "src/reasoner.py", "Diagnosis, confidence, sequencing, trade-offs, targets"],
    ["6. Response", "UI + JSON API", "Phased plan, recs, provenance [KB-ID], .md export"],
], widths=[0.9 * inch, 1.9 * inch, 3.8 * inch])

H("4. Knowledge system (critical requirement)")
B(["32 evidence cards: soil pH/SOC/moisture, land use/cover, species richness/habitat diversity, "
   "temperature/rainfall, pollution/deforestation — plus eDNA (KB26) and soil-card (KB27) protocols.",
   "Sources: FAO, IPCC AR6, IPBES 2016/2019/2023, UNCCD, Ramsar, CBD + peer-reviewed meta-analyses.",
   "Each card: intervention, mechanism, metrics, effect size, horizon, confidence, source, region fit, "
   "conditions, contraindications. Validated by <i>python -m knowledge.build_index</i>."])
Fig(A + "benchmark.png", 5.0, "retrieval benchmark: BM25+synonyms 7/7 vs TF-IDF 5/7.")
P("The two adversarial farmer paraphrases ('white crust on field, salty' → KB16; 'field floods every "
  "monsoon' → KB28) miss on TF-IDF and hit on BM25 — the measured case for the default backend. "
  "Full method + table: <i>knowledge/retrieval_benchmark.md</i>.", small)

H("5. Conversational intelligence")
B(["Vague input ('biodiversity is declining') → targeted clarifying questions, never a guess.",
   "Multi-turn memory per session id; JSON overrides memory; new text merges in.",
   "<i>measure_next</i> ranks missing inputs by decision impact, driving follow-ups.",
   "Inputs: free text, structured JSON (/assess), geo-coordinates with region inference."])
Fig(A + "ui_chat.png", 6.2, "Chat Scientist tab running the semi-arid wheat demo (?tab=chat&demo=1).")

H("6. Evidence-backed, multi-metric recommendations")
P("Each recommendation: WHAT / WHY (mechanism) / metrics / expected effect / horizon / confidence + "
  "score / reference [KB-ID]. Wheat demo (SOC 0.3%, low rain, monoculture): legume intercrop → SOC "
  "+15–25% (FAO; Poeplau &amp; Don 2015) [KB01]; bunds + pond → moisture +25–40% (UNCCD; IPCC) [KB04]. "
  "Diagnosis chains variables; plans sequence chemistry → water → biology, with trade-offs.")
Fig(A + "ui_assess.png", 6.2, "Structured Assess tab: phased plan, targets, recs, provenance (?tab=assess&demo=1).")

H("7. Knowledge grounding surface (for judges)")
B(["GET /knowledge/search — scores + matched terms for any query.",
   "GET /provenance?ids= — exact cited cards. 12 pytest tests + green CI on every push."])
Fig(A + "ui_kb.png", 6.2, "Knowledge explorer tracing 'white crust salty field' to KB16.")

H("8. API reference")
Tbl([
    ["Endpoint", "Purpose"],
    ["POST /chat", "Text + memory; clarifying Qs when incomplete"],
    ["POST /assess", "Structured JSON site → full scientific report"],
    ["GET /knowledge/search", "Retrieval trace (scores, matched terms)"],
    ["GET /provenance?ids=", "Exact evidence cards cited"],
    ["GET /sessions/{sid}", "Conversation history"],
    ["GET /health, /integrations/status, /docs", "Status + interactive docs"],
], widths=[2.4 * inch, 4.2 * inch])

H("9. Evaluation summary")
Tbl([
    ["Metric", "Result", "Verify"],
    ["Retrieval benchmark", "BM25 7/7, TF-IDF 5/7", "knowledge/retrieval_benchmark.md"],
    ["Latency (median)", "BM25 2.3 ms; assess() 2.7 ms; HTTP 13.4 ms", "ARCHITECTURE.md"],
    ["Tests", "12/12 pass", "python -m pytest tests -q; CI"],
    ["Variables combined", "6 (wheat demo)", "POST /assess variables_count"],
    ["Offline", "Identical, no network", "Disconnect + rerun demo"],
], widths=[1.6 * inch, 2.4 * inch, 2.6 * inch])

H("10. Local setup (2 minutes)")
B(["pip install -r requirements.txt",
   "python -m pytest tests -q",
   "python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 (or double-click run_local.ps1)",
   "Open http://127.0.0.1:8000 — shareable demos: ?tab=chat&amp;demo=1, ?tab=assess&amp;demo=1, ?tab=kb&amp;demo=1&amp;q=..."])
P("GitHub: " + REPO + " — no deployment, keys, or credentials required.", link)

doc.build(S)
print("pdf done")

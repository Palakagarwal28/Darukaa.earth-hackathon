"""Draw docs diagrams with PIL only. Run: python docs_assets/make_diagrams.py"""
from PIL import Image, ImageDraw, ImageFont

BG = (14, 25, 19); BOX = (22, 46, 33); LINE = (70, 160, 110); TXT = (233, 242, 234)
MUT = (157, 191, 169); ACC = (70, 192, 126); GOLD = (232, 182, 76)

def F(sz):
    for p in ("C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf"):
        try:
            return ImageFont.truetype(p, sz)
        except Exception:
            pass
    return ImageFont.load_default()

def T(d, x, y, s, sz, color):
    d.text((x, y), s, font=F(sz), fill=color)

def box(d, xy, title, subs, accent, w=300, h=110):
    x, y = xy
    d.rounded_rectangle([x, y, x + w, y + h], 14, fill=BOX, outline=accent, width=3)
    d.line([x, y + 6, x, y + h - 6], fill=accent, width=5)
    T(d, x + 16, y + 10, title, 22, TXT)
    yy = y + 44
    for s in subs:
        T(d, x + 16, yy, s, 17, MUT)
        yy += 24

def arrow(d, x1, y1, x2, y2, label=""):
    d.line([x1, y1, x2, y2], fill=LINE, width=3)
    d.polygon([(x2 - 12, y2 - 7), (x2 - 12, y2 + 7), (x2, y2)], fill=LINE)
    if label:
        T(d, (x1 + x2) / 2 - 40, (y1 + y2) / 2 - 28, label, 15, MUT)

def architecture(path):
    W, H = 1500, 980
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    T(d, 60, 30, "Darukaa.Earth - System Architecture", 34, TXT)
    T(d, 60, 80, "Deterministic science engine + RAG evidence. No generic LLM-only path.", 20, MUT)
    y = 150
    box(d, (60, y), "1. Input", ["text (chat)", "JSON (/assess)", "geo lat,lon (bonus)"], ACC)
    box(d, (420, y), "2. Conversation", ["slot-filling Qs", "SQLite memory", "measure-next"], ACC)
    box(d, (780, y), "3. Enrichment", ["geo -> region", "Open-Meteo (flagged)", "user data wins"], ACC)
    arrow(d, 360, y + 55, 420, y + 55)
    arrow(d, 720, y + 55, 780, y + 55)
    y2 = 360
    box(d, (150, y2), "4. Knowledge Retriever", ["32 evidence cards", "BM25 + synonyms (7/7)", "score + matched terms"], GOLD, w=340, h=130)
    box(d, (560, y2), "5. Reasoning Engine", ["multi-metric diagnosis", "confidence + sequencing", "trade-offs + targets"], ACC, w=340, h=130)
    box(d, (970, y2), "6. Response", ["action plan + recs", "provenance [KB-ID]", ".md export"], ACC, w=340, h=130)
    arrow(d, 940, y + 110, 940, y2 - 20, "site metrics")
    arrow(d, 490, y2 + 65, 560, y2 + 65)
    arrow(d, 900, y2 + 65, 970, y2 + 65)
    y3 = 620
    box(d, (150, y3), "Knowledge Base", ["FAO - IPCC - IPBES", "UNCCD - Ramsar - CBD", "build_index validates"], GOLD, w=340, h=130)
    box(d, (560, y3), "Optional LLM", ["rephrase only", "keeps [KB-ID]", "off by default"], ACC, w=340, h=130)
    box(d, (970, y3), "Judge surface", ["/knowledge/search trace", "12 tests green CI", "3-tab UI + /docs"], ACC, w=340, h=130)
    arrow(d, 320, y2 + 130, 320, y3, "retrieve")
    arrow(d, 1140, y2 + 130, 1140, y3 - 100, "ground")
    T(d, 60, H - 60, "Repo: github.com/Palakagarwal28/Darukaa.earth-hackathon", 19, MUT)
    im.save(path)

def benchmark(path):
    W, H = 900, 520
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    T(d, 60, 30, "Retrieval benchmark (7 queries, top-2 must hit)", 26, TXT)
    T(d, 60, 72, "5 keyword + 2 adversarial farmer paraphrases", 19, MUT)
    base = 430
    bw = 150
    for i, item in enumerate([("TF-IDF  5/7", 5 / 7, (200, 120, 120)), ("BM25+syn  7/7", 1.0, ACC)]):
        label, val, col = item
        x = 180 + i * 320
        h = int(val * 280)
        d.rectangle([x, base - h, x + bw, base], fill=col)
        T(d, x + 8, base - h - 38, label, 22, TXT)
        T(d, x + 45, base + 12, "{:.0%}".format(val), 20, MUT)
    d.line([100, base, 800, base], fill=LINE, width=2)
    T(d, 60, H - 50, "Flips: 'white crust' -> KB16, 'floods' -> KB28 (TF-IDF missed both)", 18, MUT)
    im.save(path)

if __name__ == "__main__":
    architecture("docs_assets/architecture.png")
    benchmark("docs_assets/benchmark.png")
    print("diagrams done")

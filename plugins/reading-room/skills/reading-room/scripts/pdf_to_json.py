#!/usr/bin/env python3
"""PDF kitabı Reading Room veri şemasına (data.json) dönüştürür.

Kullanım:
  python3 pdf_to_json.py kitap.pdf -o data.json
  python3 pdf_to_json.py kitap.pdf -o data.json --offset -6 --chapters bolumler.json
  python3 pdf_to_json.py kitap.pdf --inspect          # yalnızca tanı bilgisi yazdırır

Seçenekler:
  --offset N        Kitap sayfa no = PDF sayfa sırası (1'den) + N. Verilmezse
                    üst/alt bilgideki sayfa numaralarından tahmin edilir.
  --from P/--to P   Yalnızca bu PDF sayfa aralığını işle (1'den başlar).
  --chapters F      Bölümleri elle ver: [{"title":..,"author":..,"page":kitap_sayfası}, ...]
                    Verilmezse büyük puntolu satırlar bölüm başlığı sayılır.
  --body-size S     Gövde yazı boyutunu elle ver (tahmin yanlışsa).

Gerekenler: pdfplumber (pip install pdfplumber).
Taranmış (resim) PDF'lerde metin katmanı yoksa önce OCR gerekir.
"""
import argparse, collections, html, json, re, sys

FRONT = {"tr": "Başlangıç", "en": "Front matter"}

try:
    import pdfplumber
except ImportError:
    sys.exit("pdfplumber gerekli: pip install pdfplumber")

NOTE_MARK = r"(?:\d{1,3}|[*∗†‡§])"
SENT_END = tuple('.?!:;"”»)')


def is_italic(fn):
    return bool(re.search(r"Italic|Oblique|It\b|-It|Ital", fn or "", re.I))


def is_bold(fn):
    return bool(re.search(r"Bold|Black|Heavy|Semibold|Demi|-Bd|\bBd\b", fn or "", re.I))


def norm_repeat(t):
    return re.sub(r"\d+", "#", re.sub(r"\s+", " ", t.strip().lower()))


def esc(t):
    return html.escape(t, quote=False)


def with_spaces(chars):
    """PDF'te boşluk karakteri yoksa harf aralığından boşluk ekler."""
    out = []
    for c in chars:
        if out and c["text"] != " " and out[-1]["text"] != " ":
            p = out[-1]
            if c["x0"] - p["x1"] > min(c["size"], p["size"]) * 0.18:
                sp = dict(p)
                sp["text"] = " "
                out.append(sp)
        out.append(c)
    return out


class Line:
    __slots__ = ("chars", "text", "x0", "x1", "top", "bottom", "size", "pdf_page")

    def __init__(self, chars, pdf_page):
        self.chars = chars
        self.pdf_page = pdf_page
        self.text = "".join(c["text"] for c in chars)
        self.x0 = min(c["x0"] for c in chars)
        self.x1 = max(c["x1"] for c in chars)
        self.top = min(c["top"] for c in chars)
        self.bottom = max(c["bottom"] for c in chars)
        sizes = collections.Counter(round(c["size"], 1) for c in chars if c["text"].strip())
        self.size = sizes.most_common(1)[0][0] if sizes else 0


def page_lines(page, pno):
    out = []
    for ln in page.extract_text_lines(return_chars=True, strip=True):
        chars = with_spaces(sorted((c for c in ln["chars"] if c.get("text")), key=lambda c: c["x0"]))
        if chars and "".join(c["text"] for c in chars).strip():
            out.append(Line(chars, pno))
    out.sort(key=lambda l: (round(l.top), l.x0))
    return out


def runs_html(chars, body_size, page_no, sup_out):
    """Karakterleri <i>/<b>/<sup> içeren HTML'e çevirir."""
    out, cur, buf = [], (False, False), []
    base = collections.Counter(round(c["bottom"]) for c in chars if c["size"] >= body_size * 0.85)
    baseline = base.most_common(1)[0][0] if base else None

    def flush():
        if not buf:
            return
        raw = "".join(buf)
        core = raw.rstrip(" ")
        trail = raw[len(core):]
        t = esc(core)
        it, bd = cur
        if bd:
            t = "<b>" + t + "</b>"
        if it:
            t = "<i>" + t + "</i>"
        out.append(t + trail)
        buf.clear()

    i = 0
    while i < len(chars):
        c = chars[i]
        small = c["size"] < body_size * 0.82 and c["text"].strip()
        raised = baseline is not None and c["bottom"] < baseline - 1.0
        if small and raised and re.match(NOTE_MARK, c["text"]):
            j = i
            m = ""
            while j < len(chars) and chars[j]["size"] < body_size * 0.82 and chars[j]["text"].strip():
                m += chars[j]["text"]
                j += 1
            if re.fullmatch(NOTE_MARK + "+", m):
                flush()
                out.append('<sup data-p="%d">%s</sup>' % (page_no, esc(m)))
                sup_out.append((page_no, m))
                i = j
                continue
        st = (is_italic(c.get("fontname")), is_bold(c.get("fontname")))
        if st != cur and c["text"].strip():
            flush()
            cur = st
        buf.append(c["text"])
        i += 1
    flush()
    h = "".join(out)
    return re.sub(r"</i><i>|</b><b>", "", h)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("-o", "--out", default="data.json")
    ap.add_argument("--lang", choices=sorted(FRONT), default="tr", help="arayüz dili (başlıksız ilk bölümün adı için)")
    ap.add_argument("--offset", type=int)
    ap.add_argument("--from", dest="pfrom", type=int, default=1)
    ap.add_argument("--to", dest="pto", type=int)
    ap.add_argument("--chapters")
    ap.add_argument("--body-size", type=float)
    ap.add_argument("--inspect", action="store_true")
    a = ap.parse_args()

    pdf = pdfplumber.open(a.pdf)
    n = len(pdf.pages)
    pto = min(a.pto or n, n)
    pages = []  # (pno, height, width, lines)
    for pno in range(a.pfrom, pto + 1):
        p = pdf.pages[pno - 1]
        pages.append((pno, p.height, p.width, page_lines(p, pno)))
    if not any(ls for *_, ls in pages):
        sys.exit("PDF'te metin katmanı yok (taranmış olabilir). Önce OCR uygulayın (ör. ocrmypdf).")

    # --- gövde yazı boyutu ---
    cnt = collections.Counter()
    for *_, ls in pages:
        for l in ls:
            cnt[l.size] += len(l.text)
    body = a.body_size or cnt.most_common(1)[0][0]

    # --- tekrarlayan üst/alt bilgi + sayfa numarası ---
    rep = collections.Counter()
    for pno, H, W, ls in pages:
        seen = set()
        for l in ls:
            if l.top < H * 0.09 or l.bottom > H * 0.91:
                k = norm_repeat(l.text)
                if k not in seen:
                    rep[k] += 1
                    seen.add(k)
    min_rep = max(3, len(pages) * 0.2)
    pairs = []
    for pno, H, W, ls in pages:
        keep = []
        for l in ls:
            edge = l.top < H * 0.09 or l.bottom > H * 0.91
            t = l.text.strip()
            if edge and re.fullmatch(r"[-–—\s]*\d{1,4}[-–—\s]*", t):
                pairs.append(int(re.sub(r"\D", "", t)) - pno)
                continue
            if edge and rep[norm_repeat(t)] >= min_rep:
                m = re.search(r"^\d{1,4}\b|\b\d{1,4}$", t)
                if m:
                    pairs.append(int(m.group()) - pno)
                continue
            keep.append(l)
        ls[:] = keep
    if a.offset is not None:
        offset = a.offset
        off_src = "elle verildi"
    elif pairs:
        offset, c = collections.Counter(pairs).most_common(1)[0]
        off_src = "tahmin (%d/%d sayfada tutarlı)" % (c, len(pairs))
    else:
        offset, off_src = 0, "bulunamadı, 0 varsayıldı"

    def bookpage(pno):
        return pno + offset

    # --- dipnot bloklarını ayır ---
    notes = collections.defaultdict(list)
    for pno, H, W, ls in pages:
        body_ls = [l for l in ls if abs(l.size - body) < body * 0.12]
        last_body = max((l.bottom for l in body_ls), default=0)
        foot = [l for l in ls if l.size < body * 0.9 and l.top > H * 0.45 and l.top >= last_body - 1]
        if not foot:
            continue
        ls[:] = [l for l in ls if l not in foot]
        bp = bookpage(pno)
        cur = None
        for l in foot:
            t = l.text.strip()
            first_small = l.chars[0]["size"] < l.size * 0.9
            m = re.match(r"^(" + NOTE_MARK + r")[\s.)]+(.*)$", t)
            if not m and first_small:
                m = re.match(r"^(" + NOTE_MARK + r")(\S.*)$", t)
            if m:
                rest_chars = l.chars[len(m.group(1)):]
                while rest_chars and rest_chars[0]["text"] in " .)":
                    rest_chars = rest_chars[1:]
                cur = {"m": m.group(1), "h": runs_html(rest_chars, l.size, bp, [])}
                notes[str(bp)].append(cur)
            elif cur is not None:
                prev = cur["h"]
                txt = runs_html(l.chars, l.size, bp, [])
                if prev.endswith("-") and txt[:1].islower():
                    cur["h"] = prev[:-1] + txt
                else:
                    cur["h"] = prev + " " + txt
            else:  # önceki sayfadan taşan dipnot
                prevp = str(bookpage(pno - 1))
                if notes.get(prevp):
                    notes[prevp][-1]["h"] += " " + runs_html(l.chars, l.size, bp, [])

    # --- satırları bloklara çevir ---
    left = collections.Counter()
    right = collections.Counter()
    gaps = collections.Counter()
    for pno, H, W, ls in pages:
        for i, l in enumerate(ls):
            if abs(l.size - body) < body * 0.12:
                left[round(l.x0)] += 1
                right[round(l.x1)] += 1
                if i and abs(ls[i - 1].size - body) < body * 0.12:
                    gaps[round(l.top - ls[i - 1].bottom, 1)] += 1
    lm = left.most_common(1)[0][0] if left else 0
    nbody = sum(left.values()) or 1
    indented_style = sum(c for x, c in left.items() if body * 0.6 < x - lm < body * 4) / nbody > 0.03
    rm = max((x for x, c in right.items() if c >= right.most_common(1)[0][1] * 0.3), default=10000)
    gap = gaps.most_common(1)[0][0] if gaps else body * 0.4

    manual = None
    if a.chapters:
        manual = sorted(json.load(open(a.chapters, encoding="utf-8")), key=lambda c: c["page"])

    chapters = []
    sups = []

    def new_chapter(title, page, author=""):
        chapters.append({"title": title, "author": author, "page": page if page >= 1 else None, "blocks": []})

    if manual is None:
        new_chapter(FRONT[a.lang], bookpage(pages[0][0]))
    blk = None  # açık paragraf
    pending_pg = None
    mi = 0
    for pno, H, W, ls in pages:
        bp = bookpage(pno)
        if manual is not None:
            while mi < len(manual) and manual[mi]["page"] <= bp:
                c = manual[mi]
                new_chapter(c["title"], c["page"], c.get("author", ""))
                chapters[-1]["blocks"].append({"t": "h1", "h": esc(c["title"])})
                if c.get("author"):
                    chapters[-1]["blocks"].append({"t": "h2", "h": "<b>" + esc(c["author"]) + "</b>"})
                blk = None
                mi += 1
            if not chapters:
                new_chapter(FRONT[a.lang], bp)
        pending_pg = '<span class="pg" data-p="%d"></span>' % bp if bp >= 1 else None
        prev = None
        i = 0
        while i < len(ls):
            l = ls[i]
            t = l.text.strip()
            heading = manual is None and l.size >= body * 1.25 and len(t) < 160
            if heading:
                parts = [t]
                while i + 1 < len(ls) and ls[i + 1].size >= body * 1.25 and ls[i + 1].top - l.bottom < l.size * 1.2:
                    i += 1
                    l = ls[i]
                    parts.append(l.text.strip())
                title = " ".join(parts)
                if chapters and not any(b["t"] in ("p", "h1") for b in chapters[-1]["blocks"]) and chapters[-1]["title"] == FRONT[a.lang]:
                    chapters.pop()
                new_chapter(title, bp)
                chapters[-1]["blocks"].append({"t": "h1", "h": (pending_pg or "") + esc(title)})
                pending_pg = None
                blk, prev = None, l
                i += 1
                continue
            sub = abs(l.size - body) < body * 0.25 and all(is_bold(c.get("fontname")) for c in l.chars if c["text"].strip()) \
                and (l.x0 - lm) > 20 and len(t) < 90
            centered = (l.x0 - lm) > 30 and (rm - l.x1) > 30 and len(t) < 60
            line_html = runs_html(l.chars, body, bp, sups)
            if sub or (centered and (prev is None or l.top - prev.bottom > gap * 2.5)):
                chapters[-1]["blocks"].append({"t": "h2" if sub else "c", "h": (pending_pg or "") + line_html})
                cb = chapters[-1]["blocks"]
                if sub and len(cb) == 2 and cb[0]["t"] == "h1" and not chapters[-1]["author"]:
                    chapters[-1]["author"] = re.sub(r"<[^>]+>", "", line_html).strip()
                pending_pg = None
                blk, prev = None, l
                i += 1
                continue
            new_para = (
                blk is None
                or (l.x0 - lm) > body * 0.6
                or (prev is not None and l.top - prev.bottom > gap * 2.2)
                or (not indented_style and prev is not None and prev.x1 < rm - body * 3
                    and prev.text.rstrip().endswith(SENT_END))
            )
            if prev is None and blk is not None and (l.x0 - lm) <= body * 0.6:
                new_para = False  # sayfa başında paragraf devam ediyor
            if new_para:
                blk = {"t": "p", "h": ""}
                chapters[-1]["blocks"].append(blk)
            if pending_pg:
                blk["h"] += pending_pg if blk["h"] == "" or blk["h"].endswith(" ") else " " + pending_pg
                pending_pg = None
            h = blk["h"]
            if h.endswith("­"):
                h = h[:-1]
            elif re.search(r"\w-$", h) and line_html[:1].islower():
                h = h[:-1]
            elif h and not h.endswith(" ") and not h.endswith("</span>"):
                h += " "
            blk["h"] = h + line_html
            prev = l
            i += 1

    for ch in chapters:
        for b in ch["blocks"]:
            b["h"] = re.sub(r"\s+", " ", b["h"].replace("­", "")).strip()
    chapters = [c for c in chapters if c["blocks"]]

    data = {"chapters": chapters, "notes": dict(notes)}
    nmatch = 0
    for p, m in sups:
        if any(n["m"] == m for d in (0, 1, -1, 2, -2) for n in notes.get(str(p + d), [])):
            nmatch += 1
    rep_ = {
        "pdf_sayfa": "%d-%d" % (a.pfrom, pto),
        "govde_punto": body,
        "sayfa_ofseti": "%d (%s)" % (offset, off_src),
        "bolum": len(chapters),
        "paragraf": sum(1 for c in chapters for b in c["blocks"] if b["t"] == "p"),
        "dipnot_isareti": len(sups),
        "dipnot_metni": sum(len(v) for v in notes.values()),
        "eslesen_isaret": nmatch,
        "bolumler": [(c["page"], c["title"][:60]) for c in chapters],
    }
    print(json.dumps(rep_, ensure_ascii=False, indent=1), file=sys.stderr)
    if a.inspect:
        return
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    print("Yazıldı: " + a.out, file=sys.stderr)


if __name__ == "__main__":
    main()

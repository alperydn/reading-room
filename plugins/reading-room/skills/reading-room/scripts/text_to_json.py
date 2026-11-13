#!/usr/bin/env python3
"""Düz metin, Markdown, DOCX ya da EPUB dosyasını Reading Room veri şemasına çevirir.

Kullanım:
  python3 text_to_json.py kitap.epub -o data.json
  python3 text_to_json.py kitap.md   -o data.json

DOCX/EPUB önce pandoc ile Markdown'a çevrilir (pandoc kurulu olmalı).
Kurallar:
  "# Başlık"   → yeni bölüm (h1)      "## Alt başlık" → h2
  Boş satır    → yeni paragraf        *italik*, **kalın** korunur
  [^n] / [^n]: → dipnot
Düz metinde (.txt) tamamı büyük harf olan kısa satırlar bölüm başlığı sayılır.
Bu kaynaklarda kitap sayfa numarası olmadığından sayfa işareti konmaz.
"""
import argparse, html, json, os, re, subprocess, sys

FRONT = {"tr": "Başlangıç", "en": "Front matter"}


def to_markdown(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in (".md", ".markdown"):
        return open(path, encoding="utf-8").read()
    if ext == ".txt":
        out = []
        for ln in open(path, encoding="utf-8").read().splitlines():
            s = ln.strip()
            if s and len(s) < 80 and s.upper() == s and re.search(r"[A-ZÇĞİÖŞÜ]", s):
                out += ["", "# " + s, ""]
            else:
                out.append(ln)
        return "\n".join(out)
    try:
        r = subprocess.run(["pandoc", path, "-t", "markdown-smart-raw_html-native_divs-native_spans-bracketed_spans-link_attributes-header_attributes",
                            "--wrap=none"], capture_output=True, text=True, check=True)
    except FileNotFoundError:
        sys.exit("Bu dosya türü için pandoc gerekli.")
    return r.stdout


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", s)
    s = re.sub(r"(?<![\w_])_(?!\s)(.+?)(?<!\s)_(?![\w_])", r"<i>\1</i>", s)
    s = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", s)           # bağlantıları düz metne
    s = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", s)                 # görselleri at
    s = re.sub(r"\\([\\`*_{}\[\]()#+\-.!'\"])", r"\1", s)     # markdown kaçışları
    return s


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src")
    ap.add_argument("-o", "--out", default="data.json")
    ap.add_argument("--lang", choices=sorted(FRONT), default="tr", help="arayüz dili (başlıksız ilk bölümün adı için)")
    a = ap.parse_args()

    md = to_markdown(a.src)
    notes_src = {}

    def grab(m):
        notes_src[m.group(1)] = m.group(2).strip()
        return ""
    md = re.sub(r"^\[\^([^\]]+)\]:\s*(.*(?:\n(?:    |\t).*)*)", grab, md, flags=re.M)

    chapters, notes = [], {}
    paras = re.split(r"\n\s*\n", md)
    for raw in paras:
        t = " ".join(x.strip() for x in raw.strip().splitlines())
        if not t or re.fullmatch(r"[-*_\s]{3,}", t):
            continue
        m = re.match(r"^(#{1,6})\s+(.*?)\s*#*$", t)
        new_ch = bool(m) and (len(m.group(1)) == 1 or not chapters)
        if new_ch:
            title = re.sub(r"\[\^[^\]]+\]", "", m.group(2)).strip()
            chapters.append({"title": title, "author": "", "page": None, "blocks": []})
        elif not chapters:
            chapters.append({"title": FRONT[a.lang], "author": "", "page": None, "blocks": []})
        ci = len(chapters)

        def sup(mm):
            # görünen işaret: bölüm içinde 1, 2, 3… (kaynaktaki kimlik ne olursa olsun)
            lst = notes.setdefault(str(ci), [])
            num = str(len(lst) + 1)
            lst.append({"m": num, "h": inline(notes_src.get(mm.group(1), ""))})
            return '<sup data-p="%d">%s</sup>' % (ci, num)
        if m:
            h = re.sub(r"\[\^([^\]]+)\]", sup, inline(m.group(2)))
            chapters[-1]["blocks"].append({"t": "h1" if new_ch else "h2", "h": h})
            if not new_ch and len(chapters[-1]["blocks"]) == 2 and not chapters[-1]["author"]:
                chapters[-1]["author"] = re.sub(r"<[^>]+>", "", h).strip()
            continue
        t = re.sub(r"^>\s?", "", t)
        h = re.sub(r"\[\^([^\]]+)\]", sup, inline(t))
        chapters[-1]["blocks"].append({"t": "p", "h": h})

    json.dump({"chapters": chapters, "notes": notes}, open(a.out, "w", encoding="utf-8"), ensure_ascii=False)
    print("Yazıldı: %s (%d bölüm, %d paragraf, %d dipnot)" % (
        a.out, len(chapters), sum(1 for c in chapters for b in c["blocks"] if b["t"] == "p"),
        sum(len(v) for v in notes.values())), file=sys.stderr)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Şablonu (assets/sablon.html) kitap verisiyle doldurup tek bir HTML sayfası üretir.

Kullanım:
  python3 build_page.py --data data.json --gloss gloss.json --config config.json -o kitap.html

config.json alanları (yalnızca "title" zorunlu):
  title        Kitap adı (sekme başlığı ve üst çubuk)
  lang         Arayüz ve yapay zekâ cevaplarının dili: "tr" (varsayılan) ya da "en"
  book         Yapay zekâya verilen künye: '"Kitap Adı" (Yazar; Türkçe çeviri)'
  storePrefix  Tarayıcı belleği öneki, kitaba özgü ve kısa: "ks_"
  locale       Kitap metninin dili (büyük/küçük harf, sözlük eşleştirme). Varsayılan: lang
  hidden       Varsayılan olarak gizli bölümlerin indeksleri (0'dan): [0, 5]
  persona      Yapay zekâ istemlerinin ilk cümlesi
  audience     "… birinin rahatça anlayacağı" kalıbına girecek ifade: "hukuk bilgisi olmayan"
  termHint     Kelime açıklamasında terimler için ek yönerge
  smallWords   Başlıklarda küçük kalacak bağlaçlar/edatlar
"""
import argparse, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "..", "assets", "sablon.html")
BLOCK_TYPES = {"h1", "h2", "c", "p"}
LANGS = {"tr": "Reading Room", "en": "Reading Room"}


def tr_lower(s, locale):
    if locale == "tr":
        s = s.replace("I", "ı").replace("İ", "i")
    return s.lower()


def dump(obj):
    # </script> dizisi JSON bloğunu erken kapatmasın
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def check(data, gloss, cfg):
    errs, warns = [], []
    chs = data.get("chapters")
    if not isinstance(chs, list) or not chs:
        errs.append("data.chapters boş ya da liste değil")
        chs = []
    for i, c in enumerate(chs):
        for k in ("title", "page", "blocks"):
            if k not in c:
                errs.append("bölüm %d: '%s' alanı yok" % (i, k))
        for j, b in enumerate(c.get("blocks", [])):
            if b.get("t") not in BLOCK_TYPES:
                errs.append("bölüm %d blok %d: geçersiz tür %r" % (i, j, b.get("t")))
            if not isinstance(b.get("h"), str):
                errs.append("bölüm %d blok %d: 'h' metin değil" % (i, j))
    if not isinstance(data.get("notes", {}), dict):
        errs.append("data.notes sözlük olmalı")
    html_all = " ".join(b.get("h", "") for c in chs for b in c.get("blocks", []))
    sups = re.findall(r'<sup data-p="(-?\d+)">([^<]+)</sup>', html_all)
    notes = data.get("notes", {})
    miss = [(p, m) for p, m in sups
            if not any(n.get("m") == m for d in (0, 1, -1, 2, -2) for n in notes.get(str(int(p) + d), []))]
    if miss:
        warns.append("%d dipnot işaretinin metni bulunamadı (ilk birkaçı: %s)" % (len(miss), miss[:5]))
    if not re.search(r'class="pg"', html_all):
        warns.append("Sayfa işareti yok; 'Sayfaya git' gizlenecek")
    for h in cfg.get("hidden", []):
        if not (0 <= h < len(chs)):
            warns.append("hidden içindeki %r geçerli bir bölüm indeksi değil" % h)
    if len(gloss) < 30:
        warns.append("Sözlükte yalnızca %d terim var (önerilen 100–200)" % len(gloss))
    return errs, warns


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", required=True)
    ap.add_argument("--gloss")
    ap.add_argument("--config", required=True)
    ap.add_argument("--template", default=TEMPLATE)
    ap.add_argument("-o", "--out", required=True)
    a = ap.parse_args()

    data = json.load(open(a.data, encoding="utf-8"))
    cfg = json.load(open(a.config, encoding="utf-8"))
    gloss = json.load(open(a.gloss, encoding="utf-8")) if a.gloss else {}
    if not cfg.get("title"):
        sys.exit("config.json içinde 'title' gerekli")
    lang = cfg.get("lang", "tr")
    if lang not in LANGS:
        sys.exit("config.json 'lang' şunlardan biri olmalı: %s" % ", ".join(LANGS))
    loc = cfg.get("locale", lang)
    gloss = {tr_lower(k.strip(), loc): v.strip() for k, v in gloss.items() if k.strip() and v.strip()}
    data.setdefault("notes", {})

    errs, warns = check(data, gloss, cfg)
    for w in warns:
        print("UYARI: " + w, file=sys.stderr)
    if errs:
        for e in errs[:20]:
            print("HATA: " + e, file=sys.stderr)
        sys.exit(1)

    tpl = open(a.template, encoding="utf-8").read()
    title = cfg["title"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    out = (tpl.replace("{{TITLE}}", title)
              .replace("{{LANG}}", lang)
              .replace("{{APP_NAME}}", LANGS[lang])
              .replace("{{CONFIG_JSON}}", dump(cfg))
              .replace("{{DATA_JSON}}", dump(data))
              .replace("{{GLOSS_JSON}}", dump(gloss)))
    left = re.findall(r"\{\{[A-Z_]+\}\}", out)
    if left:
        sys.exit("Doldurulmamış yer tutucu: %s" % left)
    open(a.out, "w", encoding="utf-8").write(out)
    print("Yazıldı: %s (%d bölüm, %d terim, %.0f KB)" % (
        a.out, len(data["chapters"]), len(gloss), len(out.encode()) / 1024), file=sys.stderr)


if __name__ == "__main__":
    main()

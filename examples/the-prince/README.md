# The Prince — example reading room

Machiavelli, *The Prince*, translated by W. K. Marriott (1908). Public domain; text from Project Gutenberg (eBook #1232).

| File | What it is |
|---|---|
| `the-prince-reading-room.html` | The finished page. Open it in a browser. |
| `data.json` | Book text in the reading-room schema (31 chapters, 45 footnotes). |
| `gloss.json` | 160 terms with Turkish definitions. |
| `config.json` | Turkish interface, English book, translation on; translator's introduction and the two appendices hidden by default. |
| `prep_md.py` | Turns the Gutenberg text into Markdown (chapter headings, footnotes). |

Rebuild:

```sh
# prince.txt: the Project Gutenberg plain-text edition of eBook #1232, saved as src/prince.txt
python3 prep_md.py
python3 ../../plugins/reading-room/skills/reading-room/scripts/text_to_json.py prince.md -o data.json
python3 ../../plugins/reading-room/skills/reading-room/scripts/build_page.py --data data.json --gloss gloss.json --config config.json -o the-prince-reading-room.html
```

`text_to_json.py` leaves chapter authors empty; the shipped `data.json` adds them by hand.

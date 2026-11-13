# Reading Room (plugin)

This plugin adds the **reading-room** skill to Claude Code. Give Claude a PDF, EPUB, DOCX, Markdown or plain-text book and ask for a reading room: the skill extracts the text, writes a glossary of difficult terms and builds a single HTML reading page with footnotes, contents, chapter hiding, four themes and a Turkish or English interface. On claude.ai the page is published as an artifact and its AI buttons (simplify, summarize, explain, translate) work in place; elsewhere the HTML file opens in any browser without the AI features.

Install:

```text
/plugin marketplace add alperydn/reading-room
/plugin install reading-room@reading-room
```

Requirements: Python 3 with `pdfplumber` for PDFs, `pandoc` for DOCX and EPUB.

See the repository README for screenshots, installation and examples.

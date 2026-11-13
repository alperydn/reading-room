# Changelog

## 1.4.1 — 2026-11-13
- Fixed: theme buttons in the display settings showed no names.

## 1.4.0 — 2026-11-13
- Renamed from "Okuma Odası" to **Reading Room** (skill id `reading-room`).
- Claude Code plugin and marketplace manifests.

## 1.3.1 — 2026-11-13
- Clicking a blank area closes the word popover.

## 1.3.0 — 2026-11-13
- Roman numerals in chapter titles are kept (`XV`, not `Xv`).
- Footnotes in headings are handled; footnote markers are numbered per chapter for text, Markdown, DOCX and EPUB sources.
- English plurals and inflected forms match glossary entries (`principalities` → `principality`).
- Book-language text is tagged with its language, so uppercase labels and hyphenation follow that language.
- Intro and help text mention translation when it is on.
- Clear publish order on claude.ai: publish, then declare the `sample` capability.

## 1.2.1 — 2026-11-13
- Footnote markers no longer leak into text sent to the AI; paragraph breaks are kept in multi-paragraph selections.

## 1.2.0 — 2026-11-13
- Translation: when the book's language differs from the interface, tapping a word gives its equivalent in context, and *Translate* renders a selected passage. Falls back to a Google Translate link without AI.

## 1.1.0 — 2026-11-13
- English interface (`lang: "en"`), including AI prompts.
- Book language (`locale`) set separately from interface language.

## 1.0.0 — 2026-11-13
- Self-contained skill: page template, PDF and text extraction scripts, page builder, schema reference. No longer depends on a private reference page.

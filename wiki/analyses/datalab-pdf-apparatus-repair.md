---
title: Datalab PDF Apparatus Repair
type: analysis
created: 2026-08-23
updated: 2026-08-25
sources:
  - src/passage/ingest/datalab.py
  - src/passage/ingest/validation.py
  - src/passage/db/validation.py
  - tests/unit/ingest/test_datalab.py
  - tests/unit/ingest/test_validation.py
  - tests/integration/test_candidate_cli.py
  - tests/integration/test_corpus_build.py
  - docs/plans/2026-08-16-001-feat-scripture-chat-plan.md
tags: [datalab, pdf, ingestion, footnotes, provenance, repair]
---

# Datalab PDF Apparatus Repair

## Context

Datalab produced useful structured PDF output, but its reading order and inline apparatus markup were not reliable enough for direct corpus acceptance. The repair had to preserve all canonical passages, connect official footnote text to its origin anchor, and fail closed when evidence did not agree.

Raw source files, source paths, Datalab output, correction profiles, and detailed review artifacts remain outside Git. The maintainer separately approved exact inactive candidate snapshots for `candidates/`; that copy does not accept or activate either corpus.

## Observed Failure Modes

- Right-column body blocks could appear before a left-column chapter heading.
- Verse 1 had no printed verse number and required a chapter-summary boundary.
- Broad punctuation-based summary detection could discard a real first-verse fragment when that fragment used the same em-dash or date forms as a chapter summary.
- A block could contain multiple numbered verses or a verse could cross blocks and pages.
- Footnote continuation blocks were indented. Sorting them by exact horizontal position moved continuations after later entries.
- Some apparatus blocks were labeled `PageFooter` or narrow bottom `Text`, not `Footnote`.
- Datalab omitted valid inline markers, emitted false markers from italic letters, and sometimes returned the wrong marker label.
- A verse could start on one page while a later marker appeared on the next page.
- The last canonical verse could absorb every later body block when the source continued with post-canon material and no explicit terminal boundary existed.
- Superscript glyphs could sit slightly outside the Datalab block box.
- New Testament footer tables could merge chapter and verse labels, shift continuation labels into the prior verse, or separate labels from their text cells.

## Repair Method

### Canonical structure

The parser reconstructs passages in visual column order and compares the result with a packaged text-free structure manifest. The repair supports the Book of Mormon manifest and the 27-book New Testament manifest. It fails if the extracted references do not equal the selected manifest.

Canonical identity equality alone does not prove terminal fidelity: once the final expected reference has started, unrelated later text can still be appended to it. The current checkout therefore permits a digest-bound private profile to declare the first excluded PDF page and the terminal canonical reference. The parser requires that reference to be the structure manifest's final record, requires the boundary to be encountered, fails if the boundary arrives before that record, and ignores later pages only after the assertion succeeds.

Ambiguous verse-one starts use a private, digest-bound override with the exact verse-one reference, pending-fragment index, and a fingerprint of the reviewed source fragment. The fingerprint binds its PDF page, Datalab bounding box, normalized fragment text, and italic state. Duplicate, out-of-corpus, misplaced, stale, or unused rules fail closed. Default summary inference remains unchanged for chapters without an override.

### Footnote reading order

Footer blocks use three-column visual order. Blocks sort by column and vertical position, so indentation no longer changes semantic order. Tables are read column-first. `Footnote`, `PageFooter`, `Table`, and qualifying narrow bottom text blocks can supply apparatus content.

### Marker reconciliation

The parser first links an inline anchor to a footer entry by page, verse, and label. It permits a page-boundary fallback only when the verse source spans and available entry make the result unique. It can recover explicit and continuation labels from irregular table cells when the final label set is sequential. A narrow private correction profile records source-specific OCR defects that required direct PDF review. The parser applies that profile only when its stored PDF and Datalab JSON digests match the exact input bytes. The profile and its exact correction rules stay outside Git.

### PDF glyph verification

The verifier uses the dominant alphabetic font size as the body size. A valid superscript must:

- contain a lowercase label from `a` through `k`;
- use a font smaller than 80 percent of the dominant body font; and
- sit within eight PDF points of a body-text line in the same source block.

This rule permits raised superscripts near block boundaries without counting a marker from the next verse.

### Immutable output

The writer rejects a private root inside the repository. It normalizes and validates the extraction before creating repair files, then writes a mode-`0600` candidate, strict adjacent manifest, and report under the configured private root. It round-trips the result through the ordinary candidate loader before returning. Corpus validation rejects scripture passage text over 10,000 characters, more than 64 source spans, or a PDF provenance window over eight pages. The report and repair digest bind the PDF, Datalab JSON, text-free structure manifest, parser recipe, optional correction profile, normalized corpus, and findings. A changed input, recipe, profile, or finding produces a new immutable repair directory. A separately approved copy may enter `candidates/` with its exact digest and lifecycle state. Writing or copying a candidate does not accept or activate it.

## Historical Results and Current Quarantine

### Book of Mormon result reported before the terminal audit

The prior repair reported:

- 6,604 nonempty canonical passages;
- 9,826 unique official footnote anchors with nonempty text;
- 4,972 passages with at least one footnote;
- sequential anchor sets for every passage with notes;
- zero unlinked inline anchors;
- zero unmatched parsed footer entries;
- 376 Datalab-omitted markers recovered;
- one false inline marker removed; and
- one duplicate parsed footer entry ignored.

That result is not fidelity-valid. A later text-free audit found that `bofm/moro/10/34`, the final canonical record, contained 1,027,420 characters and 3,486 source spans across PDF pages 554-795. The parser had never recognized the end of the canonical work, so it appended post-canon material to the final verse. Base candidate SHA-256 `1dfd7b927e9fe5f4987a5bb5a3c8d1a0398eec6004cd01f45e86d50096a1e6b4`, formerly selected local corpus `corpus-7ba9051125f848e1aed71c46`, and typed successor SHA-256 `5207e9c1c003f12798053c667a997e8e0697495f8f4a9cafb2e112ef3aee7fa5` are quarantined from evidence and evaluation. The old corpus remains immutable but is now inactive and without editorial authority.

### New Testament

**HIGH confidence within the supplied PDF and Datalab evidence:**

- 27 books, 260 chapters, and 7,957 nonempty canonical passages;
- 10,091 unique official footnote anchors with nonempty text;
- zero ambiguous verse-one boundaries;
- zero unlinked inline anchors;
- zero unmatched parsed footer entries;
- 66 unique sequential footer anchors recovered after Datalab omitted their body markers;
- nine false body markers and two false footer continuations removed through the reviewed source profile; and
- five malformed footer labels reassigned to their verified origin passages.

The New Testament status is unchanged by the Book of Mormon diagnosis. It remains inactive, unaccepted, and `review_required`.

## Rebuilt Private Review Candidate

The current checkout implements the digest-bound terminal-page cutoff, fingerprinted verse-one overrides, writer-time corpus validation and strict manifest publication, and the 10,000-character, 64-span, and eight-page-window backstops. Published SQLite validation applies the same per-passage integrity rules before repository access. Focused regressions cover positive and negative verse-one cases, stale and invalid overrides, preservation of a legitimate final-verse continuation, exclusion of later pages, fail-closed boundary errors, writer round-trip, rejection before repair files are created, rejection of a digest-consistent oversized candidate without control-state change, and rejection of a digest-consistent legacy artifact already recorded as accepted.

The maintainer restored a matching private PDF and Datalab JSON pair. No surviving historical report proves that these are byte-identical to the original raw files, and the original correction profile is absent. Passage therefore labels the input as an exact extracted-content and source-block lineage match and labels the new source profile as reconstructed rather than original.

The private rebuild produced base candidate SHA-256 `f1d0abb72460121179ec944ee43ff3b569a2321265358dd66f20e39ee8b6aa66`: 6,604 passages, 9,826 notes, zero edges, and a 278-character terminal record with one source span on PDF page 554. All 6,603 nonterminal passage records match the quarantined candidate exactly. All 9,826 note IDs and text match; regenerated source-order fields differ while page and bounding-box evidence matches. All 6,604 passage texts reconcile exactly to their Datalab source blocks, every passage and note span maps to a source block, and all 10,280 unique PDF span regions contain nonempty overlay text.

The base result remains a private, inactive, unaccepted repair artifact. Writing and verifying it did not change control state.

## Review and Acceptance Result

The prior repair proved many internal PDF-to-parser reconciliation properties, but the missing terminal boundary shows why those properties did not establish whole-work fidelity. On 2026-08-25 the maintainer confirmed the defect, withdrew editorial authority from the affected Book of Mormon identities, and authorized repair and private rebuild.

`official-reference-v2` remains grammar-capability resolved, including typed whole-unit targets and approved digest-bound reference repairs. Rebinding those three reviewed repairs to the new base after note-ID and note-text-hash verification produced successor SHA-256 `35ed3713ee222c2778d58f3962c016ea2fef888bc0f8be4edb2b6aacf5641a4d`: 9,827 notes, 7,213 parsed reference-bearing notes, 2,614 no-reference notes, zero blockers, and 13,136 edges. Strict loading passed.

On 2026-08-25 the maintainer accepted that exact successor without manual content review after the exhaustive automated reconciliation above. Import created corpus `corpus-eb076af14ec6fff84eb40cf0`; post-import artifact, SQLite, foreign-key, record-count, and terminal-record verification passed. The maintainer then separately activated it with baseline `baseline-27ce2c9404b2a0e0df20859b`. HTTP and MCP smoke checks agree on exact lookup, lexical ordering, and official traversal.

The truthful acquisition record, exact-digest approval, import, verification, and activation are complete. The maintainer explicitly waived off-workstation backup only as a pre-acceptance gate for this single-maintainer local-only beta and accepted rebuild risk. The locked product-loop evaluation and repeated real-use gate are next; backup and recovery still gate remote delivery or irreplaceable member data.

## Reproduction

Use synthetic fixtures for routine development:

```bash
uv run pytest tests/unit/ingest/test_datalab.py -q
uv run ruff format --check .
uv run ruff check .
uv run mypy src
uv run pytest
```

A private-source repair must use explicit local source paths and a configured private root outside the repository. Do not place those values in committed commands or logs.

Source-specific correction profiles are private review artifacts. Routine repository tests use synthetic PDFs, Marker JSON, and digest-bound synthetic profiles.

## Related Pages

- [Project Overview](../overview.md)
- [Corpus Fidelity and Acceptance](../concepts/corpus-fidelity-and-acceptance.md)
- [Decision Log](../decisions.md)

## Open Questions

- Should a future independent EPUB comparison become a required acceptance check for this repaired PDF corpus?

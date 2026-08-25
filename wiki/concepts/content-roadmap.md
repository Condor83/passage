---
title: Content Roadmap
type: concept
created: 2026-08-23
updated: 2026-08-25
sources:
  - user-confirmed-conversation
  - wiki/decisions.md
  - docs/specs/2026-08-23-passage-product-specification.md
tags: [content, canon, scriptures, church-leaders, roadmap]
---

# Content Roadmap

## Confirmed Direction

Passage will grow through controlled content layers:

1. Use the Book of Mormon as a single-maintainer local beta for corpus fidelity, typed official links, retrieval, local MCP behavior, and the host-composed product-loop evaluation. Run this beta on immutable SQLite before OAuth, PostgreSQL runtime, or hosted delivery resumes.
2. Expand to the complete English LDS scripture canon. This is the minimum member-facing corpus.
3. Add the English General Conference archive as the first content family after scripture.

The Book of Mormon remains the first validation scope. This sequence does not reduce the fidelity requirements for later sources.

The prior Book of Mormon digest, source-record, acceptance, and activation conclusion was withdrawn after a terminal-boundary defect was confirmed. The repaired candidate has now passed a new exact-digest decision and separate activation, so evidence flows and the locked broad-question evaluation may resume against the active repaired pair.

The current Book of Mormon and New Testament repair candidate snapshots are version-controlled under `candidates/`. Book of Mormon base SHA-256 `1dfd7b927e9fe5f4987a5bb5a3c8d1a0398eec6004cd01f45e86d50096a1e6b4`, formerly selected local corpus `corpus-7ba9051125f848e1aed71c46`, and typed-edge successor SHA-256 `5207e9c1c003f12798053c667a997e8e0697495f8f4a9cafb2e112ef3aee7fa5` remain quarantined from evidence and evaluation. Repaired exact successor SHA-256 `35ed3713ee222c2778d58f3962c016ea2fef888bc0f8be4edb2b6aacf5641a4d` is accepted, verified, and active as corpus `corpus-eb076af14ec6fff84eb40cf0` with baseline `baseline-27ce2c9404b2a0e0df20859b`. The New Testament snapshot remains inactive, unaccepted, and `review_required`, and its official footnotes have not been converted into typed target edges.

## Shared Requirements

Every source family needs:

- stable canonical or publication identifiers;
- edition or publication identity;
- exact source provenance;
- immutable versioned ingestion;
- source-specific structure validation;
- citation-ready spans;
- typed official relationships where the source supplies them; and
- clear separation between source content and derived analysis.

## General Conference

Each accepted General Conference corpus version binds a dated official source catalog, covered conference range, acquisition cutoff, accepted Church-supplied English PDF assets, explicit inclusion rules, and known gaps. Conference-sized units are staged ingestion batches; activation still produces one complete immutable corpus version with the accumulated scripture and conference scope.

A talk uses a stable source publication identifier or canonical source URL when available. A deterministic publication fingerprint is the fallback. Speaker and title are versioned descriptive fields rather than identity by themselves. The stable talk-span citation unit remains open.

Church manuals, curriculum, books, other teaching collections, and multilingual content are deferred.

## Source-Use Boundary

Sources are manually acquired, publicly available PDFs supplied by the Church. Passage does not scrape or automatically download Church content. Public availability and noncommercial use do not establish remote redistribution permission. The owner accepts that unresolved risk for planned invite-only use, without treating it as legal clearance. Corpus acceptance still requires exact source digest and acquisition-record approval.

## Related Pages

- [Project Overview](../overview.md)
- [Decision Log](../decisions.md)
- [Corpus Fidelity and Acceptance](corpus-fidelity-and-acceptance.md)
- [Retrieval and Concept Links](retrieval-and-concept-links.md)

## Open Questions

- Which edition and acquisition contract applies to the New Testament and later works in the LDS canon?
- What dated official catalog and acquisition cutoff define the first General Conference corpus version?
- What stable citation unit should a talk use: paragraph, PDF page, publication section, or a combination?
- Will the owner seek written permission before any public delivery decision?

---
title: Phase 0 Product Loop Probe
type: analysis
created: 2026-08-23
updated: 2026-08-23
sources:
  - docs/specs/2026-08-23-passage-product-specification.md
  - src/passage/eval/phase0.py
  - tests/fixtures/evaluation/phase0_probe.json
tags: [phase-0, evaluation, atomic-tools, search-evidence, synthetic]
---

# Phase 0 Product Loop Probe

## Scope

The Phase 0 probe is a limited, source-independent feasibility check. It compares the five current atomic research operations with the combined `search_evidence` comparator. It does not evaluate host reasoning, doctrinal quality, complete-corpus discovery, derived edges, semantic retrieval, or H1.

The locked definition contains two synthetic questions and a fixed reference-pool coverage rubric. The selected synthetic corpus contains exact lookup, lexical retrieval, and official-reference traversal. Derived and experimental lanes are absent and were not graded or executed.

## Reproducible Contract

For each question, the atomic path executes, in order:

1. `get_corpus`
2. `get_passage`
3. `get_context`
4. `search_lexical`
5. `traverse_references`

The comparator executes `search_evidence` with lexical and official lanes. Every request uses one pinned corpus and retrieval configuration. Each trace records the request, applied bounds, completeness and truncation state, returned references, composite citations, source or official evidence class, and official edge evidence. The audit resolves every corpus citation and internal official target against the pinned immutable repository.

The committed definition, evaluator code, corpus, retrieval configuration, operation traces, and report content determine the report identity. Repeating the run reuses byte-identical report content.

## Measured Synthetic Result

- Corpus: `corpus-f4e1c36fa761e5233148d682`
- Retrieval configuration: `baseline-643e9e13bab2151424253dad`
- Report: `f371a8ea8c23d5c77860626a202952740a425224c2c7175ef824b6a0ea3bd170`
- Present lanes: exact, lexical, official
- Absent lanes: derived, experimental
- Citation errors: 0
- Evidence-class errors: 0
- Fatal atomic contract problems: 0
- Reference-pool coverage: 1.0 for both paths on both small synthetic questions
- H1 status: `not_evaluated`
- Promotion eligible: false

The equal coverage is only a property of this two-passage synthetic corpus and locked reference pools. It does not show that the atomic path is better than, equal to, or worse than the combined path on a real accepted corpus.

## Reproduction

Build and activate the committed synthetic EPUB in a private root outside the repository. Then run:

```bash
uv run passage phase0-probe \
  --data-dir <private-root-outside-repository> \
  --definition tests/fixtures/evaluation/phase0_probe.json
```

The report stays under the private root. Generated report files are not committed.

## Remaining Gate

Phase 2 must lock the full broad-question set and host-output rubric, accept one exact Book of Mormon source, include every lane present in that accepted corpus, and run the complete H1 comparison. Phase 0 does not authorize or satisfy that gate.

## Related Pages

- [Official Reference Grammar](../concepts/official-reference-grammar.md)
- [Retrieval and Concept Links](../concepts/retrieval-and-concept-links.md)
- [Project Overview](../overview.md)

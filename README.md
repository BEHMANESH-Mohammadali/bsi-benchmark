bsi-benchmark

Reproducible benchmark infrastructure for structured analytical frameworks

Developed by Mohammadali Behmanesh (محمدعلی بهمنش).

This repository provides a reproducible benchmark for comparing raw/default analysis with analysis guided by a structured analytical framework. The current end-to-end implementation is wired for BSI — Behmanesh Structural Index / شاخص ساختاری بهمنش.

What this tool does

The benchmark runs two analyses on the same scientific article:

1. RAW — analysis produced without the framework-specific prompt.
2. BSI — analysis produced using the BSI framework.

The two outputs are then evaluated by an independent LLM judge.

The benchmark is designed to examine analytical quality beyond output volume or surface-level performance, with attention to reproducibility, provenance, analytical realization, and incremental value.

The judge does not use BSI's internal D1–D7 or EIG terminology as its evaluation rubric. The source of the judging criteria is explicitly recorded through "criteria_source".

Current framework status

The benchmark architecture contains a framework registry intended to support multiple structured-analysis frameworks.

At present, BSI is the only framework wired end-to-end.

The repository should therefore be understood as:

«a benchmark infrastructure currently instantiated with BSI,»

rather than as a claim that the benchmark has already been empirically validated across multiple independent frameworks.

Behmanesh Structural Index (BSI)

BSI — Behmanesh Structural Index / شاخص ساختاری بهمنش is a layered, interdisciplinary framework for structural analysis of intellectual content.

It is designed to examine:

- patterns and themes
- intellectual development
- worldview and conceptual structure
- underlying mechanisms
- relationships between explicit and deeper layers of content
- analytical depth and coherence

BSI is intended to distinguish structural analytical value from merely larger or more elaborate textual output.

Repositories

- Profile / canonical identity: "BEHMANESH-Mohammadali/BEHMANESH-Mohammadali"
- Benchmark source: "BEHMANESH-Mohammadali/bsi-benchmark"
- Benchmark results: "BEHMANESH-Mohammadali/bsi-benchmark-results-bsi"
- BSI framework and prompt definitions: "BEHMANESH-Mohammadali/behmanesh-index-prompt"

Author:

Mohammadali Behmanesh / محمدعلی بهمنش

GitHub: @BEHMANESH-Mohammadali

X: @behmanesham

Reproducibility principles

The benchmark records provenance information needed to distinguish comparable runs, including:

- article identity
- provider
- analyst/generator model
- analysis mode
- judge model
- prompt version
- judging criteria source
- full-text availability
- retrieval status
- benchmark status

Results using heuristic judging are explicitly distinguishable from results judged by an LLM.

"criteria_source == "llm"" indicates an actual LLM judging pass.

"criteria_source == "heuristic_fallback"" indicates that the independent LLM judge was not successfully used and therefore should not be treated as equivalent evidence.

Supported article providers

The project currently includes providers such as:

- "arxiv"
- "openalex"
- "crossref"
- "europepmc"
- "semantic_scholar"
- "mock"
- "single_article"

Full-text availability depends on the provider. When full text is unavailable, the input may be abstract-only unless a local full-text file is supplied.

Main command

bsi-benchmark compare --help

The primary benchmark command compares RAW and BSI analyses on the same article and optionally evaluates them with an independent judge.

Rejudging existing analyses

Saved analysis checkpoints can be reused.

When the same output/checkpoint is supplied without "--fresh", successful cached analyses are not regenerated unnecessarily. Missing, failed, or otherwise invalid judging steps can be retried.

This allows judge sensitivity and robustness experiments without regenerating the underlying analyses.

Results repository

Registered benchmark evidence is maintained separately:

"BEHMANESH-Mohammadali/bsi-benchmark-results-bsi"

The results repository contains:

- registered compare results
- case studies
- aggregate CSV reports
- repeatability/drift analyses
- benchmark reports
- provenance information

The results repository is the authoritative public storage location for registered BSI benchmark evidence.

Important evidence rules

Benchmark evidence should preserve enough information to determine:

- which article was analyzed
- which text was available to the analyst
- which models were used
- which prompt/framework version was used
- how the outputs were judged
- whether the judging process was valid

Title-only records or records lacking sufficient article content should not be treated as equivalent to analyses performed with an abstract or full text.

Development environment

The project is developed and tested primarily on Android using Termux.

Typical environment:

- Python 3.11+
- Git
- Termux

License

MIT

---

Project identity

Mohammadali Behmanesh
محمدعلی بهمنش

Behmanesh Structural Index (BSI)
شاخص ساختاری بهمنش

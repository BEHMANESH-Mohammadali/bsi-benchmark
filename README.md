# BSI Benchmark

Reproducible benchmark infrastructure for structured analytical frameworks.

The current end-to-end implementation is wired for BSI — Behmanesh Structural Index / شاخص ساختاری بهمنش.

## Canonical BSI v3.5 prompt integration

The `compare` command now loads the canonical BSI v3.5 master prompt and its authoritative references directly from:

`BEHMANESH-Mohammadali/behmanesh-index-prompt`

By default it reads the `main` branch. Before the framework migration is merged, a reviewed branch can be selected explicitly:

```bash
bsi-benchmark compare \
  --provider openalex \
  --query "your research query" \
  --generators openrouter \
  --bsi-prompt-ref migration/bsi-v3.5-canonical \
  --output results/bsi_v35_run
```

After the canonicalization PR is merged, omit `--bsi-prompt-ref` and the generator will use `main`.

The loader retrieves the v3.5 master prompt and all pinned authoritative references from the same Git ref, appends article placeholders in memory, and computes SHA-256 digests. Run metadata records the prompt source, package hash, and individual reference hashes. If any required reference cannot be fetched, loading fails rather than silently falling back to an older prompt.

A local prompt can still be supplied explicitly with `--bsi-prompt-file`; when that option is used, the local file is the selected source and the remote canonical package is not loaded.

**Important:** the benchmark's separate evaluation/judging rubric is not the BSI framework's internal D1–D7 scoring engine. A BSI-guided generation run uses the prompt package; the benchmark judge remains an independent evaluation mechanism.

## What this tool does

The benchmark runs RAW/default and BSI-guided analyses on the same scientific article, then evaluates the outputs with an independent LLM judge. It records article identity, source text availability, provider, generator, judge, prompt version, prompt hashes, retrieval status, and relevant run metadata.

The benchmark is designed to examine analytical realization and incremental value, not merely output length. It is not, by itself, proof that BSI is a validated psychometric instrument.

## Framework status

BSI is currently the only framework wired end-to-end in this benchmark. The framework registry is intended to support future frameworks, but no cross-framework empirical validation is claimed.

## Supported article providers

- `arxiv`
- `openalex`
- `crossref`
- `europepmc`
- `semantic_scholar`
- `mock`
- `single_article`

Full-text availability depends on the provider. If full text is unavailable, the analysis may be abstract-only unless a local full-text file is supplied.

## Generators

Multiple generation backends are available, including OpenRouter, OpenAI, Anthropic, Gemini, Groq, DeepSeek, GapGPT, and local/mock backends. Real generation requires the relevant provider API key in the environment.

## Main command

`bsi-benchmark compare --help`

The compare command performs generation and independent judging on the same retrieved article set.

## Reproducibility and evidence rules

Each run should preserve:

- exact framework and master prompt version;
- prompt package SHA-256 and authoritative-reference hashes;
- article identity and source provenance;
- source text available to the generator;
- generator and judge model identifiers;
- generation settings when known;
- retrieval status and full-text availability;
- whether judging used an LLM or heuristic fallback.

Heuristic judging is not equivalent evidence to a successful independent LLM judging pass. The stored `criteria_source` field distinguishes these cases.

Cached checkpoints should not be reused across prompt versions unless their prompt provenance is verified as identical. Use a distinct output/checkpoint path when changing framework or prompt version.

## Repositories

- BSI framework and canonical prompts: [behmanesh-index-prompt](https://github.com/BEHMANESH-Mohammadali/behmanesh-index-prompt)
- Benchmark source: [bsi-benchmark](https://github.com/BEHMANESH-Mohammadali/bsi-benchmark)
- Registered benchmark evidence: [bsi-benchmark-results-bsi](https://github.com/BEHMANESH-Mohammadali/bsi-benchmark-results-bsi)

## Author

Mohammadali Behmanesh / محمدعلی بهمنش

GitHub: [@BEHMANESH-Mohammadali](https://github.com/BEHMANESH-Mohammadali)

X: [@behmanesham](https://x.com/behmanesham)

License: MIT

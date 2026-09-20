#!/usr/bin/env python3
"""
Validate and curate benchmark result files (both compare-cli reports
and self-compare records) from results/ into a separate results-storage
repository, then commit and push there.

--- Bugs fixed relative to the previous version of this script ---

1. Non-recursive scan (`RESULTS.glob("*.json")`) never saw files inside
   results/self_compare/ or any other subdirectory -- files already
   curated once, or written into a subfolder by hand, were silently
   invisible to every later run.

2. The top-level gate required BOTH "article" and "analyst_model" keys,
   so a compare-cli report (schema: dataset_name/results/run_metadata)
   could never pass, no matter how valid -- it was always rejected with
   "not a self-compare record ... leave it in results/, do not curate".
   The results-storage repo's own README documents a compare/ folder
   fed by this exact script; with the old code that folder could only
   ever be populated by hand, never by this script.

3. The validation logic (`walk()` checking for a nested `judge_result`
   with `criteria_source == "llm"`) was written for compare-cli's
   ComparisonCell schema. A self-compare record never contains a
   `judge_result` key anywhere (its schema is a flat `criteria` list of
   analyst-chosen raw_score/bsi_score pairs -- see
   self_compare/models.py). So for every self-compare record this walk
   found nothing to flag and `errors` stayed empty regardless of the
   record's actual quality (e.g. a record with no criteria, once one
   slips past the CLI's own loader, or hand-edited afterwards) --
   the only real gate was the top-level key check from bug #2.

This version:

  * scans `results/` recursively (`rglob`), skipping `*.checkpoint.json`
    and anything already inside the destination directories;
  * classifies each `<name>.json` (with a required `<name>.md` sibling)
    as "compare" or "self" from its actual schema;
  * validates a self-compare record by loading it through the exact
    same `SelfComparisonIO().load()` the `self-compare` CLI command
    itself uses, instead of a second, independently-maintained
    validator that can drift out of sync with it. A record that
    doesn't have `raw_analysis_text`/`bsi_analysis_text` still curates
    (the CLI itself only warns, never refuses) but is flagged as
    "not independently checkable" in the run's own output;
  * validates a compare-cli report by reconstructing the real
    ComparisonReport/ComparisonResult/ComparisonCell dataclasses and
    using their own `.complete` / `.incomplete_reasons` -- the same
    definition of "publishable" the library already enforces elsewhere
    (e.g. in `cli.py`'s own MockGenerator guard), instead of a
    hand-rolled duplicate that can silently disagree with it;
  * curates into `compare/` and `self_compare/` *inside a separate
    results-storage repository* pointed to by
    `BSI_BENCHMARK_RESULTS_REPO`, not back into this source repo's own
    `results/` -- this is what the results repo's README describes.
    If the env var isn't set, falls back to `results/curated/` inside
    this repo with a loud warning, so the script still runs (just
    without the separate-repo publish step) before that variable is
    configured.
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from bsi_benchmark.self_compare import SelfComparisonIO  # noqa: E402
from bsi_benchmark.comparison.result import (  # noqa: E402
    ComparisonReport,
    ComparisonResult,
    ComparisonCell,
)
from bsi_benchmark.models.article import Article  # noqa: E402
from bsi_benchmark.models.analysis import Analysis  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"

_RESULTS_REPO_ENV = "BSI_BENCHMARK_RESULTS_REPO"
_dest_env = os.environ.get(_RESULTS_REPO_ENV, "").strip()
if _dest_env:
    DEST_REPO = Path(_dest_env).expanduser().resolve()
    DEST_IS_SEPARATE = True
else:
    DEST_REPO = RESULTS / "curated"
    DEST_IS_SEPARATE = False

DEST_COMPARE = DEST_REPO / "compare"
DEST_SELF = DEST_REPO / "self_compare"


def classify_result(data: dict) -> str:
    """
    Distinguish the two known result schemas without conflating them.

    Returns "compare", "self", or "unknown".
    """
    if not isinstance(data, dict):
        return "unknown"

    if (
        isinstance(data.get("results"), list)
        and "run_metadata" in data
        and ("dataset_name" in data or "source_url" in data)
    ):
        return "compare"

    if "article" in data and "analyst_model" in data:
        return "self"

    return "unknown"


def _cell_from_dict(d: dict) -> ComparisonCell:
    analysis = Analysis(**d["analysis"]) if d.get("analysis") else None
    return ComparisonCell(
        generator=d.get("generator", ""),
        mode=d.get("mode", ""),
        analysis=analysis,
        metadata=d.get("metadata") or {},
        judge_result=d.get("judge_result"),
        scores=d.get("scores") or {},
        failed=bool(d.get("failed", False)),
    )


def _report_from_dict(data: dict) -> ComparisonReport:
    results = []
    for r in data.get("results", []):
        article = Article(**r["article"])
        cells = [_cell_from_dict(c) for c in r.get("cells", [])]
        results.append(
            ComparisonResult(
                article=article,
                cells=cells,
                article_id=r.get("article_id", ""),
            )
        )
    return ComparisonReport(
        dataset_name=data.get("dataset_name", ""),
        results=results,
        source_url=data.get("source_url"),
        run_metadata=data.get("run_metadata"),
    )


def validate_compare(data: dict) -> list:
    """Return a list of human-readable problems; empty list == valid."""
    try:
        report = _report_from_dict(data)
    except (KeyError, TypeError) as e:
        return [f"could not reconstruct compare-cli report: {e}"]

    if not report.complete:
        return report.incomplete_reasons or ["report.complete is False"]

    return []


def validate_self(path: Path) -> tuple:
    """
    Returns (errors, warnings). Reuses the real SelfComparisonIO loader
    so this validator can never silently drift from what the
    'self-compare' CLI command itself accepts.
    """
    io = SelfComparisonIO()
    try:
        record = io.load(str(path))
    except (ValueError, FileNotFoundError, KeyError) as e:
        return [str(e)], []

    warnings = []
    if not record.has_source_texts():
        warnings.append(
            "raw_analysis_text/bsi_analysis_text missing -- record is "
            "self-reported only, not independently checkable against "
            "the actual analysis text"
        )
    if record.overall_winner not in ("raw", "bsi", "tie"):
        warnings.append(
            f"overall_winner={record.overall_winner!r} is not one of "
            "raw/bsi/tie"
        )

    return [], warnings


def iter_candidates():
    dest_names = {DEST_COMPARE.resolve(), DEST_SELF.resolve()}
    for p in sorted(RESULTS.rglob("*.json")):
        if not p.is_file():
            continue
        if p.name.endswith(".checkpoint.json"):
            continue
        if any(parent.resolve() in dest_names for parent in p.parents):
            continue
        yield p


def run(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd, check=True)


def main():
    if not DEST_IS_SEPARATE:
        print(
            f"WARNING: {_RESULTS_REPO_ENV} is not set -- curating into "
            f"{DEST_REPO} instead of a separate results-storage repo. "
            f"Set {_RESULTS_REPO_ENV} to a clone of the framework's "
            f"results repository before running this in normal use."
        )

    DEST_COMPARE.mkdir(parents=True, exist_ok=True)
    DEST_SELF.mkdir(parents=True, exist_ok=True)

    curated_compare = 0
    curated_self = 0
    rejected = 0
    skipped_unknown = 0

    for src_json in iter_candidates():
        src_md = src_json.with_suffix(".md")
        if not src_md.exists():
            continue

        try:
            data = json.loads(src_json.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            rejected += 1
            print(f"INVALID: {src_json} -- invalid JSON: {e}")
            continue

        kind = classify_result(data)

        if kind == "compare":
            errors = validate_compare(data)
            dest_dir = DEST_COMPARE
        elif kind == "self":
            errors, warnings = validate_self(src_json)
            if warnings:
                print(f"NOTE: {src_json.name}")
                for w in warnings:
                    print(f"  - {w}")
            dest_dir = DEST_SELF
        else:
            skipped_unknown += 1
            print(f"SKIP (unrecognized schema): {src_json}")
            continue

        if errors:
            rejected += 1
            print(f"INVALID ({kind}): {src_json.name}")
            for e in errors:
                print(f"  - {e}")
            continue

        dst_json = dest_dir / src_json.name
        dst_md = dest_dir / src_md.name
        shutil.copy2(src_json, dst_json)
        shutil.copy2(src_md, dst_md)

        if kind == "compare":
            curated_compare += 1
        else:
            curated_self += 1
        print(f"CURATED ({kind}): {src_json.name}")

    print()
    print(f"Curated compare results : {curated_compare}")
    print(f"Curated self-compare    : {curated_self}")
    print(f"Rejected/invalid        : {rejected}")
    print(f"Skipped (unknown schema): {skipped_unknown}")

    run(["git", "add", "compare", "self_compare"], cwd=DEST_REPO)

    staged = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=DEST_REPO,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()

    if not staged:
        print("Nothing new to commit.")
        return 0

    print()
    print("===== STAGED FOR AUTOMATIC COMMIT =====")
    print(staged)

    run(["git", "diff", "--cached", "--check"], cwd=DEST_REPO)
    run(
        ["git", "commit", "-m", "Register validated benchmark results"],
        cwd=DEST_REPO,
    )

    print()
    print("===== COMMIT COMPLETE =====")
    run(["git", "status", "-sb"], cwd=DEST_REPO)

    print()
    print("===== PUSH =====")
    try:
        run(["git", "push"], cwd=DEST_REPO)
        print("Pushed.")
    except subprocess.CalledProcessError as e:
        print(f"Push failed (commit is still saved locally): {e}")
        print("Run 'git push' manually once the issue is resolved.")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

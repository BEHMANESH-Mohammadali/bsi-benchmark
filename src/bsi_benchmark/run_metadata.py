"""
Run-level metadata for a ComparisonReport, so a report can stand on its
own as evidence: which exact code produced it, when, and with what known
methodological limitations -- rather than a bare score table with no
provenance.

This does NOT make BSI scores a validated psychometric instrument. It
makes the *report* an honest, checkable record of what was run.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from .version import __version__ as TOOL_VERSION

METHODOLOGY_NOTE = (
    "Scores/judgements come from an independent LLM judge (see "
    "comparison/judge.py) instructed not to reuse BSI's own D1-D7/EIG "
    "vocabulary and to choose its own evaluation criteria. If no judge "
    "model is available or its response cannot be parsed, the run falls "
    "back to a simple keyword-presence heuristic -- the stored record's "
    "own 'criteria_source' field ('llm' vs 'heuristic_fallback') always "
    "says honestly which one produced a given result. Neither path is a "
    "validated measurement of analytical quality until checked against "
    "independent human judgement on a representative sample."
)


def _git_commit(cwd: Optional[str] = None) -> Optional[str]:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=cwd, capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return None


def _git_dirty(cwd: Optional[str] = None) -> Optional[bool]:
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=cwd, capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            return bool(result.stdout.strip())
    except (OSError, subprocess.SubprocessError):
        pass
    return None


@dataclass
class RunMetadata:
    tool_version: str
    git_commit: Optional[str]
    git_dirty: Optional[bool]
    run_timestamp_utc: str
    methodology_note: str = METHODOLOGY_NOTE
    # Model/generation configuration, so "GPT-5.5" alone (no version, no
    # date, no temperature) is never the whole provenance record. All
    # optional and None by default -- populated by the caller (cli.py)
    # from whatever it actually knows for that run; this module has no
    # way to discover them on its own.
    provider_name: Optional[str] = None
    model_version: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    prompt_version: Optional[str] = None
    # Which analysis framework produced the "treatment" arm of this run.
    # Defaults to "bsi" today because that's the only framework this
    # tool currently drives end-to-end, but the field exists so a future
    # framework (see ROADMAP.md, plugin architecture) does not require a
    # schema change to be distinguishable in stored records.
    prompt_source: Optional[str] = None
    prompt_sha256: Optional[str] = None
    prompt_reference_hashes: Optional[dict] = None
    framework_name: str = "bsi"

    @classmethod
    def capture(
        cls,
        repo_dir: Optional[str] = None,
        *,
        provider_name: Optional[str] = None,
        model_version: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        prompt_version: Optional[str] = None,
        framework_name: str = "bsi",
        prompt_source: Optional[str] = None,
        prompt_sha256: Optional[str] = None,
        prompt_reference_hashes: Optional[dict] = None,
    ) -> "RunMetadata":
        """
        Build a RunMetadata snapshot for 'right now'.

        git_commit / git_dirty are None (not False) if this isn't a git
        checkout or git isn't available -- callers should render that as
        an explicit "unknown", not silently treat it as clean/absent.

        The generation-config kwargs are all optional and default to
        None: this function cannot discover them itself (it doesn't call
        any generator), so it only records what the caller passes in.
        """
        return cls(
            tool_version=TOOL_VERSION,
            git_commit=_git_commit(repo_dir),
            git_dirty=_git_dirty(repo_dir),
            run_timestamp_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            provider_name=provider_name,
            model_version=model_version,
            temperature=temperature,
            max_tokens=max_tokens,
            prompt_version=prompt_version,
            prompt_source=prompt_source,
            prompt_sha256=prompt_sha256,
            prompt_reference_hashes=prompt_reference_hashes,
            framework_name=framework_name,
        )

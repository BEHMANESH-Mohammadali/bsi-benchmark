"""Load BSI prompts from local files or the canonical public framework repository.

Remote loading pins the master prompt and its authoritative references to one
Git ref and records SHA-256 digests. It does not rewrite any source file.
"""
from __future__ import annotations

import hashlib
from urllib.parse import quote

import requests

PLACEHOLDER_BLOCK = (
    "\n\n---\n"
    "[bsi-benchmark: article injected below by the compare command]\n"
    "Title: {title}\n"
    "Abstract: {abstract}\n"
    "DOI: {doi}\n"
    "\nFull text (may be empty if unavailable):\n{full_text}\n"
)

CANONICAL_REPOSITORY = "BEHMANESH-Mohammadali/behmanesh-index-prompt"
CANONICAL_REF = "main"
MASTER_PROMPT_PATH = "MASTER_PROMPT_BSI_v3.5.md"
AUTHORITATIVE_REFERENCES = {
    "architectural_invariants": "ARCHITECTURAL_INVARIANTS_BSI_v3.5.md",
    "execution_architecture": "BSI_3.5_Execution_Architecture.md",
    "output_contract": "docs/specification/ANALYTICAL_OUTPUT_CONTRACT_LAYERC_v3.5.md",
    "canonical_specification_matrix": "docs/specification/CANONICAL_SPECIFICATION_MATRIX_v3.5.md",
    "core_behmanesh": "CORE-BEHMANESH/v1.0/CORE_BEHMANESH_v1.0.md",
    "bio": "Ontology/BIO_v1.0.md",
    "sop": "SOP_Intellectual_Content_Analysis_v3.4.2.md",
    "eig": "CORE-BEHMANESH/Shared_Components/EIG/Epistemic_Integrity_Gap_Analyzer_v1.0.md",
    "ecc": "CORE-BEHMANESH/Shared_Components/EIG/Epistemic_Confidence_Calibration_v2.0.md",
    "reig": "CORE-BEHMANESH/Shared_Components/EIG/Recursive_EIG_v1.0.md",
    "calculation_formula": "BSI_Calculation_Formula_Hybrid_v3x.md",
}


def load_bsi_prompt(path: str, *, label: str = "prompt-file") -> str:
    """Load a local prompt file and append article placeholders if absent."""
    with open(path, encoding="utf-8") as f:
        content = f.read()

    has_title = "{title}" in content
    has_abstract = "{abstract}" in content
    if has_title and has_abstract:
        print(f"[{label}] '{path}': article placeholders found, using as-is.")
        return content
    if has_title or has_abstract:
        missing = "{abstract}" if has_title else "{title}"
        raise ValueError(f"[{label}] '{path}' has only one article placeholder; missing {missing}.")
    print(f"[{label}] '{path}': appending article placeholders in memory.")
    return content + PLACEHOLDER_BLOCK


def load_canonical_bsi_v35(
    repository: str = CANONICAL_REPOSITORY,
    ref: str = CANONICAL_REF,
    *,
    timeout: int = 30,
) -> tuple[str, dict]:
    """Fetch v3.5 master prompt and authoritative references from one Git ref."""
    if "/" not in repository:
        raise ValueError("repository must be in owner/name form")
    owner, name = repository.split("/", 1)
    base = f"https://raw.githubusercontent.com/{owner}/{name}/refs/heads/{quote(ref, safe='/')}/"

    def fetch(path: str) -> dict[str, str]:
        response = requests.get(base + path, timeout=timeout)
        response.raise_for_status()
        response.encoding = "utf-8"
        content = response.text
        return {
            "path": path,
            "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
            "content": content,
        }

    master = fetch(MASTER_PROMPT_PATH)
    references = {key: fetch(path) for key, path in AUTHORITATIVE_REFERENCES.items()}

    # Include references verbatim so the generator receives the same pinned
    # authoritative material, rather than relying on unresolved relative links.
    sections = [
        master["content"],
        "\n\n# PINNED AUTHORITATIVE BSI v3.5 REFERENCES\n",
    ]
    for key, item in references.items():
        sections.append(
            f"\n\n---\n## Authoritative reference: {key} ({item['path']})\n"
            f"SHA-256: {item['sha256']}\n\n{item['content']}"
        )
    prompt = "\n".join(sections) + PLACEHOLDER_BLOCK
    provenance = {
        "framework_version": "3.5",
        "repository": repository,
        "ref": ref,
        "master_prompt": {"path": master["path"], "sha256": master["sha256"]},
        "authoritative_references": {
            key: {"path": item["path"], "sha256": item["sha256"]}
            for key, item in references.items()
        },
    }
    provenance["package_sha256"] = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    return prompt, provenance

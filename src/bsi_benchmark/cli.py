
"""
Command-line interface for BSI Benchmark.
"""

import argparse
import os

from .version import __version__
from .benchmark import BenchmarkRunner
from .export import ExportManager
from bsi_benchmark.errors import ProviderError


def main() -> int:

    parser = argparse.ArgumentParser(prog="bsi-benchmark")

    sub = parser.add_subparsers(dest="command")

    run = sub.add_parser(
        "run",
        help="Fetch articles for a query and run a Dataset-level evaluator "
             "(currently only 'basic', which counts articles).",
    )

    run.add_argument("--provider", required=True)
    run.add_argument("--query", required=True)
    run.add_argument("--format", default=None)
    run.add_argument("--output", default=None)

    evaluate = sub.add_parser(
        "evaluate",
        help="Score a BSI-generated analysis against its source article "
             "using the 'bsi' evaluator. Input is a JSON file matching the "
             "AnalyzedDataset schema (see datasets/analyzed_dataset.py) -- "
             "for a single pre-generated analysis. For an automated "
             "multi-model benchmark run, use 'compare' instead.",
    )
    evaluate.add_argument(
        "--input",
        required=True,
        help="Path to an AnalyzedDataset JSON file.",
    )

    compare = sub.add_parser(
        "compare",
        help="Automated benchmark: fetch articles, call one or more LLM "
             "generators under one or more prompt modes (e.g. raw vs bsi), "
             "score every combination with the BSI evaluator, and produce "
             "a comparison report. Requires the relevant API key env var "
             "(ANTHROPIC_API_KEY / OPENAI_API_KEY) for real generators, or "
             "use --generators mock for an offline dry run.",
    )
    compare.add_argument("--provider", required=True, help="e.g. crossref, arxiv, mock")
    compare.add_argument("--query", required=True)
    compare.add_argument(
        "--judge",
        default=None,
        help="Judge generator name. If omitted, each generator judges its own output.",
    )
    compare.add_argument(
        "--judge-model",
        default=None,
        help="Optional model identifier used by the explicit judge generator.",
    )
    compare.add_argument(
        "--fresh",
        action="store_true",
        help="Ignore any existing checkpoint at --output and start a new "
             "run (an existing checkpoint/report, if present, is archived "
             "with a timestamp suffix rather than overwritten).",
    )

    compare.add_argument(
        "--generators", required=True,
        help="Comma-separated generator names registered in generation.registry "
             "(e.g. 'anthropic,openai' or 'mock' for an offline dry run).",
    )
    compare.add_argument(
        "--raw-prompt-file",
        help="Path to a plain baseline prompt template ({title}/{abstract} "
             "placeholders). If omitted, a generic default is used.",
    )
    compare.add_argument(
        "--bsi-prompt-file",
        default=None,
        help="Optional local BSI master prompt file. If omitted, the canonical "
             "BSI v3.5 master prompt and authoritative references are fetched "
             "from --bsi-prompt-repo at --bsi-prompt-ref.",
    )
    compare.add_argument(
        "--bsi-prompt-repo",
        default="BEHMANESH-Mohammadali/behmanesh-index-prompt",
        help="GitHub owner/repository for the canonical BSI prompt (default: official repository).",
    )
    compare.add_argument(
        "--bsi-prompt-ref",
        default="main",
        help="Git ref for the canonical BSI prompt (default: main; use a reviewed migration branch before merge).",
    )

    compare.add_argument(
    "--limit",
    type=int,
    default=None,
    help="Limit number of articles returned by provider"
)
    compare.add_argument(
        "--full-text-file",
        default=None,
        help="Optional UTF-8 full-text file to attach to every fetched article "
             "for this benchmark run. The file is not modified. Takes "
             "priority over --fetch-full-text if both are given.",
    )
    compare.add_argument(
        "--fetch-full-text",
        action="store_true",
        help="Instead of supplying a local file, ask the provider to fetch "
             "the real full text of each article itself (currently "
             "supported for --provider arxiv only: downloads the PDF and "
             "extracts text). Per-article failures (no PDF, scanned/"
             "image-only PDF, network error) are printed as warnings and "
             "that article falls back to abstract-only rather than "
             "aborting the whole run. Ignored if --full-text-file is set.",
    )

    compare.add_argument(
        "--bsi-source-url",
        default=None,
        help="Link to the canonical BSI prompt file, printed in the report "
             "so readers can inspect the exact canonical prompt. Override if "
             "you benchmarked against a different branch/file. "
             "Pass '' to omit the link entirely.",
    )
    compare.add_argument(
        "--temperature", type=float, default=None,
        help="Record the generation temperature used, if you know it "
             "(this tool does not set it -- it just records it in "
             "run_metadata so 'GPT-5.5' alone is never the whole "
             "provenance record).",
    )
    compare.add_argument(
        "--max-tokens", type=int, default=None,
        help="Record the max_tokens setting used, if you know it.",
    )
    compare.add_argument(
        "--prompt-version", default="3.5",
        help="Prompt version recorded in provenance (default: 3.5).",
    )
    compare.add_argument("--output", required=True, help="Output file path prefix (writes .md and .json).")

    self_compare = sub.add_parser(
        "self-compare",
        help="Record an analyst's own comparison of their raw-vs-bsi "
             "analysis of one article. The analyst chooses their own "
             "criteria (this tool imposes no rubric) and supplies a "
             "raw_score/bsi_score per criterion; the winner per criterion "
             "is derived from those two scores, not separately asserted. "
             "Input is a JSON file -- see examples/self_compare_example.json "
             "for the expected shape and examples/self_compare_prompt.md "
             "for the instructions to give the analyst.",
    )
    self_compare.add_argument(
        "--input", required=True,
        help="Path to a self-comparison JSON file filled in by the analyst.",
    )
    self_compare.add_argument(
        "--output", required=True,
        help="Output file path prefix (writes .md and .json). The .json "
             "output is the canonical stored record (results/ is the "
             "conventional place to keep these); the .md is for reading.",
    )

    stats = sub.add_parser(
        "stats",
        help="Aggregate multiple self-compare JSON records (from "
             "'self-compare' output) into descriptive statistics: mean "
             "raw/bsi scores, bootstrap 95%% CI on the difference, "
             "Cohen's d_z, and a Wilcoxon signed-rank test. Pure Python, "
             "no scipy dependency (so it runs on Termux). Purely "
             "descriptive of the self-reported data -- see the caveats "
             "section of its own output for what it does NOT establish.",
    )
    stats.add_argument(
        "--input", required=True, nargs="+",
        help="One or more self-compare .json record files (the output "
             "of 'self-compare --output ...'), e.g. results/self_compare/*.json",
    )
    stats.add_argument("--output", required=True, help="Output file path prefix (writes .md).")

    frameworks = sub.add_parser(
        "frameworks",
        help="List analysis frameworks registered with this tool. Today "
             "only 'bsi' is registered end-to-end; this command exists "
             "so the tool's framework list is inspectable rather than "
             "hardcoded and invisible -- see ROADMAP.md for the plan to "
             "add more.",
    )

    args = parser.parse_args()

    print(f"BSI Benchmark {__version__}")

    if args.command == "run":

        runner = BenchmarkRunner()

        try:
            result = runner.run(
                args.provider,
                args.query,
            )
        except ProviderError as e:
            print(f"ERROR: {e}")
            return 1

        print(f"Provider : {result.dataset.provider}")
        print(f"Query    : {result.dataset.query}")
        print(f"Articles : {len(result.dataset.articles)}")

        # export integration (Ma's local addition, kept)
        if args.format and args.output:
            ExportManager().export(
                result,
                args.format,
                args.output,
            )
            print(f"Report written to {args.output}")

        return 0

    if args.command == "evaluate":
        from bsi_benchmark.datasets import AnalyzedDatasetIO
        from bsi_benchmark.evaluation import EvaluationEngine

        dataset = AnalyzedDatasetIO().load(args.input)
        engine = EvaluationEngine()

        print(f"Dataset  : {dataset.name}")
        print(f"Items    : {dataset.size}")
        print()

        for i, item in enumerate(dataset.items, start=1):
            result = engine.evaluate("bsi", item)
            title = item.article.title or "(untitled)"
            print(f"[{i}] {title}")
            for dim in ("D1", "D2", "D3", "D4", "D5", "D6", "D7", "BSI"):
                print(f"    {dim:16s} {result.scores[dim]:.3f}")
            print(f"    {'grounding_ratio':16s} {result.scores['grounding_ratio']:.3f}")
            print(f"    {'tag_coverage':16s} {result.scores['tag_coverage']:.3f}")
            print()

        return 0

    if args.command == "compare":
        from bsi_benchmark.pipeline import PipelineRunner
        from bsi_benchmark.comparison import ComparisonSpec, CrossModelRunner, render_markdown
        from bsi_benchmark.comparison.json_export import save as save_json
        from bsi_benchmark.prompt_loader import (
            load_bsi_prompt, load_canonical_bsi_v35,
        )
        from bsi_benchmark.run_metadata import RunMetadata
        from dataclasses import asdict as _asdict

        DEFAULT_RAW_PROMPT = (
            "Analyze the following academic article. Give a concise, "
            "factual analysis of its main claims and contribution.\n\n"
            "Title: {title}\nAbstract: {abstract}\n\n"
            "Full text (may be empty if unavailable):\n{full_text}"
        )

        raw_prompt = DEFAULT_RAW_PROMPT
        if args.raw_prompt_file:
            raw_prompt = load_bsi_prompt(args.raw_prompt_file, label="raw-prompt-file")

        prompt_provenance = None
        if args.bsi_prompt_file:
            bsi_prompt = load_bsi_prompt(
                args.bsi_prompt_file, label="bsi-prompt-file"
            )
            import hashlib
            prompt_provenance = {
                "framework_version": args.prompt_version,
                "source": os.path.abspath(args.bsi_prompt_file),
                "package_sha256": hashlib.sha256(
                    bsi_prompt.encode("utf-8")
                ).hexdigest(),
            }
        else:
            try:
                bsi_prompt, prompt_provenance = load_canonical_bsi_v35(
                    repository=args.bsi_prompt_repo,
                    ref=args.bsi_prompt_ref,
                )
            except Exception as e:
                print(f"ERROR loading canonical BSI v3.5 prompt package: {e}")
                return 1
            print(
                f"BSI PROMPT : v{prompt_provenance['framework_version']} "
                f"from {prompt_provenance['repository']}@{prompt_provenance['ref']}"
            )
            print(
                f"PROMPT SHA : {prompt_provenance['package_sha256']}"
            )

        try:
            dataset = PipelineRunner().run(
                args.provider,
                args.query,
                args.limit,
            )
        except ProviderError as e:
            print(f"ERROR fetching dataset: {e}")
            return 1

        if args.full_text_file:
            full_text_path = os.path.abspath(args.full_text_file)

            if not os.path.isfile(full_text_path):
                print(f"ERROR: full-text file not found: {full_text_path}")
                return 1

            try:
                with open(full_text_path, "r", encoding="utf-8") as f:
                    full_text = f.read()
            except OSError as e:
                print(f"ERROR reading full-text file: {e}")
                return 1

            if not full_text.strip():
                print(f"ERROR: full-text file is empty: {full_text_path}")
                return 1

            for article in dataset.articles:
                article.full_text = full_text
                quality = dict(article.input_quality or {})
                quality["has_full_text"] = True
                quality["full_text_chars"] = len(full_text)
                quality["full_text_source"] = full_text_path
                article.input_quality = quality

            print(
                f"FULLTEXT   : {len(full_text):,} chars "
                f"from {full_text_path}"
            )

        elif args.fetch_full_text:
            from bsi_benchmark.providers import ProviderManager

            fulltext_provider = ProviderManager().create(args.provider)

            if not hasattr(fulltext_provider, "fetch_fulltext"):
                print(
                    f"WARNING: --fetch-full-text given but provider "
                    f"'{args.provider}' does not support automatic "
                    f"full-text fetching yet (only 'arxiv' does). "
                    f"Continuing with abstract-only for all articles."
                )
            else:
                for article in dataset.articles:
                    quality = dict(article.input_quality or {})
                    try:
                        full_text = fulltext_provider.fetch_fulltext(article)
                    except Exception as e:
                        print(
                            f"WARNING: full-text fetch failed for "
                            f"'{article.title}': {e}. Falling back to "
                            f"abstract-only for this article."
                        )
                        quality["has_full_text"] = False
                        quality["full_text_fetch_error"] = str(e)
                        article.input_quality = quality
                        continue

                    article.full_text = full_text
                    quality["has_full_text"] = True
                    quality["full_text_chars"] = len(full_text)
                    quality["full_text_source"] = "provider_fetch:" + args.provider
                    article.input_quality = quality
                    print(
                        f"FULLTEXT   : {len(full_text):,} chars fetched "
                        f"for '{article.title}'"
                    )

        spec = ComparisonSpec(
            generators=[g.strip() for g in args.generators.split(",") if g.strip()],
            prompt_modes={"raw": raw_prompt, "bsi": bsi_prompt},
            judge=args.judge,
            judge_model=args.judge_model,
        )

        print(f"Provider   : {dataset.provider}")
        print(f"Query      : {dataset.query}")
        print(f"Articles   : {len(dataset.articles)}")
        if dataset.skipped_count:
            print(
                f"Skipped    : {dataset.skipped_count} article(s) with no "
                f"usable title/abstract (not sent to any generator): "
                f"{', '.join(dataset.skipped_titles[:5])}"
                + (" ..." if dataset.skipped_count > 5 else "")
            )
        if not dataset.articles:
            print(
                "ERROR: no articles with a usable title/abstract were found "
                "for this query/provider/limit combination. Try a different "
                "query, provider, or a higher --limit."
            )
            return 1
        print(f"Generators : {', '.join(spec.generators)}")
        print(f"Modes      : {', '.join(spec.prompt_modes.keys())}")
        print("Running... (this calls a real API for each non-mock generator; may take a while)")
        print()

        from bsi_benchmark.comparison.checkpoint import (
            checkpoint_path as _checkpoint_path_for,
            archive_existing_checkpoint,
        )

        ckpt_path = _checkpoint_path_for(args.output)
        if args.fresh:
            archive_existing_checkpoint(args.output)
        elif os.path.exists(ckpt_path):
            print(f"Resuming from checkpoint: {ckpt_path}")

        if args.bsi_source_url is not None:
            source_url = args.bsi_source_url or None
        elif prompt_provenance and "repository" in prompt_provenance:
            source_url = (
                f"https://github.com/{prompt_provenance['repository']}/blob/"
                f"{prompt_provenance['ref']}/MASTER_PROMPT_BSI_v3.5.md"
            )
        else:
            source_url = None

        report = CrossModelRunner().run(
            dataset, spec,
            source_url=source_url,
            run_metadata=_asdict(RunMetadata.capture(
                repo_dir=os.path.dirname(os.path.abspath(__file__)),
                temperature=args.temperature,
                max_tokens=args.max_tokens,
                prompt_version=args.prompt_version,
                prompt_source=(
                    f"{prompt_provenance['repository']}@{prompt_provenance['ref']}"
                    if prompt_provenance and "repository" in prompt_provenance
                    else prompt_provenance.get("source") if prompt_provenance else None
                ),
                prompt_sha256=(
                    prompt_provenance.get("package_sha256")
                    if prompt_provenance else None
                ),
                prompt_reference_hashes=(
                    {
                        key: value["sha256"]
                        for key, value in prompt_provenance.get(
                            "authoritative_references", {}
                        ).items()
                    } if prompt_provenance else {}
                ),
            )),
        
            checkpoint_path=ckpt_path,)

        if any(
            c.generator == "mock"
            for r in report.results
            for c in r.cells
        ):
            print("ERROR: MockGenerator output is test-only and cannot be stored as benchmark evidence.")
            return 2

        md_path = f"{args.output}.md"
        json_path = f"{args.output}.json"

        out_dir = os.path.dirname(md_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(render_markdown(report))
        save_json(report, json_path)

        print(f"Wrote {md_path}")
        print(f"Wrote {json_path}")

        return 0

    if args.command == "self-compare":
        from bsi_benchmark.self_compare import SelfComparisonIO, render_markdown as render_self_compare_md
        from bsi_benchmark.run_metadata import RunMetadata
        from dataclasses import asdict as _asdict

        io = SelfComparisonIO()
        try:
            record = io.load(args.input)
        except (ValueError, FileNotFoundError, KeyError) as e:
            print(f"ERROR reading self-compare input: {e}")
            return 1

        if record.run_metadata is None:
            record.run_metadata = _asdict(
                RunMetadata.capture(repo_dir=os.path.dirname(os.path.abspath(__file__)))
            )

        print(f"Article        : {record.article_title}")
        print(f"Analyst        : {record.analyst_model}")
        print(f"Criteria       : {len(record.criteria)}")
        print(f"raw wins / bsi wins / ties : {record.raw_wins()} / {record.bsi_wins()} / {record.ties()}")
        print(f"Overall winner : {record.overall_winner}")
        if not record.has_source_texts():
            print(
                "WARNING: raw_analysis_text/bsi_analysis_text missing -- "
                "this record's scores are self-reported only, not checkable "
                "against the actual analysis text."
            )
        print()


        md_path = f"{args.output}.md"
        json_path = f"{args.output}.json"

        out_dir = os.path.dirname(md_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(render_self_compare_md(record))
        io.save(record, json_path)

        print(f"Wrote {md_path}")
        print(f"Wrote {json_path}")

        return 0

    if args.command == "stats":
        from bsi_benchmark.self_compare import SelfComparisonIO
        from bsi_benchmark.stats import aggregate, render_markdown as render_stats_md

        io = SelfComparisonIO()
        records = []
        for path in args.input:
            try:
                records.append(io.load(path))
            except (ValueError, FileNotFoundError, KeyError) as e:
                print(f"ERROR reading '{path}': {e}")
                return 1

        if not records:
            print("ERROR: no input records loaded.")
            return 1

        result = aggregate(records)

        print(f"Records : {result.n_records}")
        print(f"Pairs   : {result.n}")
        print(f"Mean diff (bsi - raw) : {result.mean_diff:.3f}")
        if result.ci95_low is not None:
            print(f"95% CI  : [{result.ci95_low:.3f}, {result.ci95_high:.3f}]")
        if result.wilcoxon_p_approx is not None:
            print(f"Wilcoxon p (approx) : {result.wilcoxon_p_approx:.4f}")
        print()

        md_path = f"{args.output}.md"
        out_dir = os.path.dirname(md_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(render_stats_md(result))

        print(f"Wrote {md_path}")

        return 0

    if args.command == "frameworks":
        from bsi_benchmark.frameworks import registry

        names = registry.list_names()
        if not names:
            print("No frameworks registered.")
            return 0

        print(f"{len(names)} framework(s) registered:\n")
        for name in names:
            fw = registry.get(name)
            print(f"- {fw.name} (version: {fw.version or 'unknown'})")
            print(f"  {fw.description}")
            print()

        return 0

    parser.print_help()

    return 0

if __name__ == "__main__":
    raise SystemExit(main())

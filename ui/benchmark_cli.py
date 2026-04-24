import argparse
import json
from pathlib import Path

from analysis_engine.comparator import HouseholdAnalysisEngine
from benchmark_engine.service import build_default_benchmark_provider
from benchmark_settings import load_benchmark_settings
from collectors.factory import get_collector
from input_engine.validators import parse_household_input
from normalizers.factory import get_normalizer
from output_engine.report_builder import build_output_payload
from source_registry.loader import load_source_registry
from storage.benchmark_db import BenchmarkDatabase
from storage.benchmark_repository import BenchmarkRepository


def _build_runtime():
    settings = load_benchmark_settings()
    registry = load_source_registry(settings.registry_path)
    repository = BenchmarkRepository(BenchmarkDatabase(settings.db_path))
    repository.initialize()
    return settings, registry, repository


def cmd_init_db(_args):
    settings, _registry, repository = _build_runtime()
    repository.initialize()
    print(f"Initialized benchmark database: {settings.db_path}")


def cmd_list_sources(_args):
    _settings, registry, _repository = _build_runtime()
    for source in registry.list_sources():
        print(
            f"{source.source_name} | type={source.source_type} | role={source.benchmark_role} "
            f"| collector={source.collector_key} | enabled={source.enabled}"
        )


def cmd_update_sources(args):
    settings, registry, repository = _build_runtime()
    source_names = [args.only] if args.only else [item.source_name for item in registry.list_sources(enabled_only=True)]

    for source_name in source_names:
        source = registry.get(source_name)
        if not source.enabled:
            print(f"Skipped disabled source: {source_name}")
            continue
        collector = get_collector(source.collector_key, settings)
        normalizer = get_normalizer(source.normalizer_key)
        collected = collector.collect(source, normalizer)
        repository.store_collected_source(source, collected)
        print(
            f"Updated {source.source_name}: {len(collected.normalized_records)} normalized records "
            f"for {collected.period_year}"
        )


def cmd_source_status(_args):
    _settings, _registry, repository = _build_runtime()
    rows = repository.list_source_status()
    if not rows:
        print("No source updates found.")
        return
    for row in rows:
        print(
            f"{row['source_name']} | status={row['status']} | fetched_at={row['fetched_at']} "
            f"| normalized={row['normalized_count']} | version={row['source_version']}"
        )


def _load_household_payload(args, settings):
    if args.input_file:
        return json.loads(Path(args.input_file).read_text(encoding="utf-8"))
    sample_path = settings.resolve_path("data/source_samples/sample_household_input.json")
    return json.loads(sample_path.read_text(encoding="utf-8"))


def cmd_demo_analysis(args):
    settings, registry, repository = _build_runtime()
    household_payload = _load_household_payload(args, settings)
    household_input = parse_household_input(household_payload)
    benchmark_provider = build_default_benchmark_provider(registry, repository)
    analysis_engine = HouseholdAnalysisEngine(benchmark_provider)
    benchmark_context, analysis_result = analysis_engine.analyze(household_input)
    output_payload = build_output_payload(household_input, benchmark_context, analysis_result)
    repository.store_analysis_snapshot(
        household_input=household_input,
        benchmark_context=benchmark_context,
        analysis_result=analysis_result,
        summary_text=output_payload["summary_text"],
    )

    print(output_payload["summary_text"])
    if args.print_json:
        print("")
        print(json.dumps(output_payload, ensure_ascii=False, indent=2))


def build_parser():
    parser = argparse.ArgumentParser(
        description="Benchmark data layer CLI for household finance comparison.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_db = subparsers.add_parser("init-db", help="Initialize the benchmark SQLite database.")
    init_db.set_defaults(func=cmd_init_db)

    list_sources = subparsers.add_parser("list-sources", help="Show configured data sources.")
    list_sources.set_defaults(func=cmd_list_sources)

    update_sources = subparsers.add_parser("update-sources", help="Collect and normalize benchmark sources.")
    update_sources.add_argument("--only", help="Update only one source_name.")
    update_sources.set_defaults(func=cmd_update_sources)

    source_status = subparsers.add_parser("source-status", help="Show latest source update status.")
    source_status.set_defaults(func=cmd_source_status)

    demo_analysis = subparsers.add_parser("demo-analysis", help="Run a sample household comparison analysis.")
    demo_analysis.add_argument("--input-file", help="JSON file with household input payload.")
    demo_analysis.add_argument("--print-json", action="store_true", help="Print the full JSON analysis payload.")
    demo_analysis.set_defaults(func=cmd_demo_analysis)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

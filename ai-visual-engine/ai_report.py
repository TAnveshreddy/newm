#!/usr/bin/env python3
"""CLI entry point for the AI Visual / Report Generation Engine.

Usage:
    python ai_report.py --data ./data/sales.csv \
        --prompt "Show monthly revenue by region as a line chart"

    python ai_report.py --data ./data \
        --prompt "Create a sales dashboard: revenue by region, monthly revenue trend, total revenue"

Set LLM_API_KEY to use a real LLM for planning; otherwise the built-in
deterministic planner is used (fully offline).
"""
import argparse
import json

from ai_report import load_data, generate_report


def main() -> None:
    parser = argparse.ArgumentParser(description="AI Ad-Hoc Reporting Engine")
    parser.add_argument("--data", required=True, help="CSV/XLSX file or folder")
    parser.add_argument("--prompt", required=True, help="Natural-language report request")
    parser.add_argument("--output", default="./generated_reports", help="Output folder")
    parser.add_argument("--no-render", action="store_true", help="Skip PNG rendering (JSON only)")
    args = parser.parse_args()

    print("\n====================================")
    print("AI AD-HOC REPORTING ENGINE")
    print("====================================\n")

    print("Loading data...")
    datasets = load_data(args.data)
    print(f"Datasets loaded: {list(datasets.keys())}\n")

    print("Understanding prompt and generating report...")
    result = generate_report(datasets, args.prompt, args.output, render=not args.no_render)

    print("\n--- Report Plan (Visual JSON) ---")
    print(json.dumps(result.plan, indent=2, default=str))

    print("\n--- Summary ---")
    print(json.dumps(result.summary(), indent=2, default=str))

    if not args.no_render:
        print("\n--- Generated files ---")
        for v in result.visuals:
            if v.ok and v.file:
                print(" ", v.file)

    print("\n====================================")
    print(f"DONE — {result.successful} succeeded, {result.failed} failed")
    print("====================================")


if __name__ == "__main__":
    main()

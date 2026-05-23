"""Command-line interface for context-optimized agents."""
from __future__ import annotations

import argparse
import json

from .diagrams import create_academic_diagram
from .llm import client_from_mode
from .metrics import MetricsSimulator
from .orchestrator import OrchestrationAgent
from .schemas import to_dict
from .utils import read_text, write_json


DEFAULT_OBJECTIVE = (
    "Design a context-optimized multi-agent workflow that routes only necessary context, "
    "enforces budgets, compresses findings upward, performs council and security review, "
    "and produces decision-memory records."
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="coa",
        description="Context-optimized multi-agent orchestration CLI",
    )
    sub = parser.add_subparsers(dest="command")

    run = sub.add_parser("run", help="Run the orchestration workflow")
    run.add_argument("objective", nargs="?", default=DEFAULT_OBJECTIVE, help="User objective to execute")
    run.add_argument("--objective-file", help="Read the objective from a text file")
    run.add_argument("--required-output", default="final synthesis", help="Required final output type")
    run.add_argument("--mode", choices=["mock", "live"], default="mock", help="Use deterministic mock mode or OpenAI live mode")
    run.add_argument("--model", default="gpt-5.5", help="Model used by all model-routed agents")
    run.add_argument("--max-parallel-agents", type=int, default=12, help="Max concurrent sub-agent executions")
    run.add_argument("--output", default="runs/workflow_result.json", help="Path for JSON workflow output")
    run.add_argument("--print-final", action="store_true", help="Print the final synthesis to stdout")

    metrics = sub.add_parser("metrics", help="Print representative expected metrics")
    metrics.add_argument("--output", help="Optional JSON output path")

    diagram = sub.add_parser("diagram", help="Generate the academic architecture diagram")
    diagram.add_argument("--output-dir", default="docs/figures", help="Directory to write SVG/PNG/PDF files")

    prompts = sub.add_parser("prompts", help="Print bundled system prompts")
    prompts.add_argument("--output", help="Optional JSON output path")

    return parser


def run_command(args: argparse.Namespace) -> int:
    objective = read_text(args.objective_file) if args.objective_file else args.objective
    llm_client = client_from_mode(args.mode)
    orchestrator = OrchestrationAgent(
        model=args.model,
        llm_client=llm_client,
        max_parallel_agents=args.max_parallel_agents,
    )
    result = orchestrator.run(objective, required_output=args.required_output)
    data = to_dict(result)
    write_json(args.output, data)
    if args.print_final:
        print(result.final_synthesis.final_answer)
        print("\nMetrics:")
        for row in result.metrics.rows:
            print(
                f"- {row.metric}: {row.brute_force} -> {row.optimized} {row.unit} "
                f"({row.improvement_pct:+.1f}% improvement)"
            )
    else:
        print(f"Wrote workflow result to {args.output}")
        print(f"Final quality score: {result.final_synthesis.quality_score:.2f}")
    return 0


def metrics_command(args: argparse.Namespace) -> int:
    metrics = MetricsSimulator().simulate()
    data = to_dict(metrics)
    if args.output:
        write_json(args.output, data)
        print(f"Wrote metrics to {args.output}")
    else:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    return 0


def diagram_command(args: argparse.Namespace) -> int:
    paths = create_academic_diagram(args.output_dir)
    print(json.dumps(paths, indent=2))
    return 0


def prompts_command(args: argparse.Namespace) -> int:
    from .prompts import SYSTEM_PROMPTS

    if args.output:
        write_json(args.output, SYSTEM_PROMPTS)
        print(f"Wrote prompts to {args.output}")
    else:
        print(json.dumps(SYSTEM_PROMPTS, indent=2, ensure_ascii=False))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    if args.command == "run":
        return run_command(args)
    if args.command == "metrics":
        return metrics_command(args)
    if args.command == "diagram":
        return diagram_command(args)
    if args.command == "prompts":
        return prompts_command(args)
    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

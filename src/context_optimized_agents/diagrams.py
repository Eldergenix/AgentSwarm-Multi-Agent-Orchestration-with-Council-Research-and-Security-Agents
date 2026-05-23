"""Publication-style diagram generation for the orchestration architecture."""
from __future__ import annotations

from pathlib import Path
from typing import Dict


def create_academic_diagram(output_dir: str | Path = "docs/figures") -> Dict[str, str]:
    """Create SVG, PNG, and PDF versions of the orchestration diagram.

    Returns a dict of format -> path.
    """
    try:
        import matplotlib.pyplot as plt
        from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle
    except Exception as exc:
        raise RuntimeError("Diagram generation requires: pip install -e .[diagram]") from exc

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(17, 10.5))
    ax.set_xlim(0, 17)
    ax.set_ylim(0, 10.5)
    ax.axis("off")

    def box(x, y, w, h, title, body="", fc="#F7FAFC", ec="#2D3748", lw=1.4, fontsize=10):
        patch = FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.028,rounding_size=0.08",
            linewidth=lw,
            edgecolor=ec,
            facecolor=fc,
        )
        ax.add_patch(patch)
        ax.text(x + w / 2, y + h - 0.18, title, ha="center", va="top", fontsize=fontsize, fontweight="bold")
        if body:
            ax.text(x + 0.18, y + h - 0.55, body, ha="left", va="top", fontsize=fontsize - 1, linespacing=1.18)
        return patch

    def arrow(x1, y1, x2, y2, text="", rad=0.0):
        arr = FancyArrowPatch(
            (x1, y1),
            (x2, y2),
            arrowstyle="-|>",
            mutation_scale=12,
            linewidth=1.2,
            color="#2D3748",
            connectionstyle=f"arc3,rad={rad}",
        )
        ax.add_patch(arr)
        if text:
            ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 0.15, text, ha="center", va="center", fontsize=8)

    ax.text(
        8.5,
        10.18,
        "Context-Optimized Multi-Agent Orchestration with Budgeted Context Routing",
        ha="center",
        va="center",
        fontsize=16,
        fontweight="bold",
    )
    ax.text(
        8.5,
        9.86,
        "A scoped-context architecture for reducing token duplication, hallucination exposure, and synthesis overhead",
        ha="center",
        va="center",
        fontsize=10,
    )

    # Main left-to-right pipeline.
    box(0.35, 8.25, 2.0, 0.9, "User Objective", "Task, constraints,\nrequired output", "#EBF8FF")
    box(2.9, 8.1, 2.25, 1.2, "Orchestration Agent", "Creates plan, roles,\nbudgets, schemas", "#E6FFFA")
    box(5.7, 8.1, 2.25, 1.2, "Context Router", "Classifies task; selects\nminimal role context", "#F0FFF4")
    box(8.5, 8.1, 2.25, 1.2, "Budget Allocator", "Input/output budgets;\nleast-context routing", "#FFFFF0")
    box(11.3, 8.1, 2.25, 1.2, "Context Auditor", "Dedupes, redacts,\nflags budget overruns", "#FFF5F5")
    box(14.05, 8.1, 2.45, 1.2, "Shared Task Capsule", "Objective, constraints,\ndefinitions, schema", "#EDF2F7")

    arrow(2.35, 8.7, 2.9, 8.7)
    arrow(5.15, 8.7, 5.7, 8.7)
    arrow(7.95, 8.7, 8.5, 8.7)
    arrow(10.75, 8.7, 11.3, 8.7)
    arrow(13.55, 8.7, 14.05, 8.7)

    # Memory layers.
    box(
        0.35,
        5.75,
        2.65,
        1.95,
        "Layered Memory",
        "Session\nProject\nUser\nWorking\nRetrieval\nDecision",
        "#F7FAFC",
    )
    arrow(1.68, 7.7, 5.85, 8.15, "selective retrieval", rad=-0.08)

    # Agent groups.
    group_y = 5.6
    box(3.4, group_y, 2.7, 1.45, "Direct Sub-Agents", "5 specialists\narchitecture, metrics,\nmemory, implementation", "#E6FFFA")
    box(6.55, group_y, 2.7, 1.45, "Council Agents", "4 councils x 5\nfactuality, reasoning,\nproduct, quality", "#F0FFF4")
    box(9.7, group_y, 2.7, 1.45, "Deep Research", "1 parent x 5\nevidence, cost, latency,\nreliability", "#EBF8FF")
    box(12.85, group_y, 2.7, 1.45, "Security Review", "1 parent x 5\nprompt injection, memory,\ntools, hallucination", "#FFF5F5")
    for x in [4.75, 7.9, 11.05, 14.2]:
        arrow(15.25, 8.1, x, group_y + 1.45, "scoped packets", rad=0.1)

    # Compression layer.
    box(
        4.45,
        3.72,
        9.2,
        0.95,
        "Hierarchical Context Compression Layer",
        "Sub-agents return 3-6 structured findings -> parent agents merge into 10-15 high-signal findings; duplicate context is removed before final synthesis.",
        "#FAF5FF",
        fontsize=10,
    )
    for x in [4.75, 7.9, 11.05, 14.2]:
        arrow(x, group_y, x, 4.67)

    # Review and final.
    box(3.55, 2.45, 3.3, 0.95, "Council Review", "Compare conclusions; resolve disagreements", "#F0FFF4")
    box(7.35, 2.45, 3.3, 0.95, "Security Review", "Permissions, policy, injection, leakage", "#FFF5F5")
    box(11.15, 2.45, 3.3, 0.95, "Final Synthesis", "Evidence, assumptions, risks, next actions", "#E6FFFA")
    arrow(7.1, 3.72, 5.2, 3.4)
    arrow(10.95, 3.72, 9.0, 3.4)
    arrow(10.65, 2.92, 11.15, 2.92)
    arrow(6.85, 2.92, 7.35, 2.92)

    box(
        11.5,
        1.05,
        2.9,
        0.85,
        "Decision Memory",
        "Store only final answer, assumptions, evidence, risks, actions",
        "#EDF2F7",
        fontsize=9,
    )
    arrow(12.8, 2.45, 12.95, 1.9)

    # Expected outputs.
    box(
        0.35,
        2.1,
        2.65,
        2.75,
        "Expected Structured Output",
        "{\n  claim, evidence[],\n  confidence, risk,\n  recommended_action\n}\n\nParent output:\ncompressed_findings[],\nmaterial_disagreements[],\nduplicate_findings_removed",
        "#F7FAFC",
        fontsize=9,
    )

    # Metrics table.
    table_x, table_y = 0.35, 0.35
    table_w, table_h = 10.15, 1.55
    ax.add_patch(Rectangle((table_x, table_y), table_w, table_h, linewidth=1.2, edgecolor="#2D3748", facecolor="#FFFFFF"))
    ax.text(table_x + 0.12, table_y + table_h - 0.22, "Representative expected improvement metrics (35-sub-agent workload)", fontsize=9, fontweight="bold", va="top")
    headers = ["Metric", "Brute-force", "Optimized", "Improvement"]
    rows = [
        ["Input tokens", "~0.72M", "~0.20M", "~72% less"],
        ["Token cost", "$5.13", "$1.51", "~71% less"],
        ["Duplicate context", "42%", "10%", "~76% less"],
        ["Latency", "47.5s", "31.2s", "~34% less"],
    ]
    col_w = [2.8, 2.25, 2.2, 2.4]
    x = table_x + 0.12
    y = table_y + table_h - 0.50
    for i, h in enumerate(headers):
        ax.text(x + sum(col_w[:i]), y, h, fontsize=8, fontweight="bold", va="top")
    for r, row in enumerate(rows):
        yy = y - 0.23 * (r + 1)
        for i, cell in enumerate(row):
            ax.text(x + sum(col_w[:i]), yy, cell, fontsize=8, va="top")

    ax.text(
        8.5,
        0.08,
        "Figure 1. Scoped context routing uses shared task capsules, private role packets, strict budgets, progressive retrieval, and hierarchical compression before final synthesis.",
        ha="center",
        va="bottom",
        fontsize=8,
    )

    svg = out / "context_orchestrator_academic_diagram.svg"
    png = out / "context_orchestrator_academic_diagram.png"
    pdf = out / "context_orchestrator_academic_diagram.pdf"
    fig.savefig(svg, bbox_inches="tight")
    fig.savefig(png, dpi=220, bbox_inches="tight")
    fig.savefig(pdf, bbox_inches="tight")
    plt.close(fig)
    return {"svg": str(svg), "png": str(png), "pdf": str(pdf)}

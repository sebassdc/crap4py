import csv
import io
import json


def crap_score(complexity, coverage_pct):
    """Compute CRAP score: CC² × (1 - coverage)³ + CC."""
    cc = float(complexity)
    uncov = 1.0 - coverage_pct / 100.0
    return cc * cc * uncov * uncov * uncov + cc


def sort_by_crap(entries):
    """Sort entries by CRAP score descending."""
    return sorted(entries, key=lambda e: e.crap, reverse=True)


def format_report(entries):
    """Format a CRAP report as a text table."""
    header = f"{'Function':<30} {'Module':<35} {'CC':>4} {'Cov%':>6} {'CRAP':>8}"
    sep = "-" * len(header)
    lines = [
        f"{e.name:<30} {e.module:<35} {e.complexity:>4} {e.coverage:>5.1f}% {e.crap:>8.1f}"
        for e in entries
    ]
    return "\n".join(["CRAP Report", "===========", header, sep] + lines + [""])


def format_json_report(entries):
    """Format a CRAP report as JSON."""
    data = {
        "tool": "crap4py",
        "entries": [
            {
                "name": e.name,
                "module": e.module,
                "complexity": e.complexity,
                "coverage": e.coverage,
                "crap": round(e.crap, 1),
            }
            for e in entries
        ],
    }
    return json.dumps(data, indent=2)


def format_markdown_report(entries):
    """Format a CRAP report as a GitHub Flavored Markdown table."""
    lines = [
        "# CRAP Report",
        "",
        "| Function | Module | CC | Cov% | CRAP |",
        "|---|---|---:|---:|---:|",
    ]
    for e in entries:
        lines.append(f"| {e.name} | {e.module} | {e.complexity} | {e.coverage:.1f}% | {e.crap:.1f} |")
    return "\n".join(lines) + "\n"


def format_csv_report(entries):
    """Format a CRAP report as CSV."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Function", "Module", "CC", "Coverage", "CRAP"])
    for e in entries:
        writer.writerow([e.name, e.module, e.complexity, f"{e.coverage:.1f}", f"{e.crap:.1f}"])
    return output.getvalue()

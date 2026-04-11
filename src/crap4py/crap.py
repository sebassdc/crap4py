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

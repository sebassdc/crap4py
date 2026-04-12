import json

from crap4py.crap import (
    crap_score,
    format_csv_report,
    format_json_report,
    format_markdown_report,
    format_report,
    sort_by_crap,
)
from crap4py.models import CrapEntry


class TestCrapScore:
    def test_full_coverage_returns_cc(self):
        # CC^2 * (1-1)^3 + CC = 0 + CC = CC
        assert crap_score(5, 100.0) == 5.0

    def test_zero_coverage_returns_cc_squared_plus_cc(self):
        # CC^2 * 1 + CC = 25 + 5 = 30
        assert crap_score(5, 0.0) == 30.0

    def test_partial_coverage(self):
        # CC=8, cov=45 -> 64 * (0.55)^3 + 8 = 64 * 0.166375 + 8 ≈ 18.648
        assert abs(crap_score(8, 45.0) - 18.648) < 0.01

    def test_trivial_fully_covered(self):
        assert crap_score(1, 100.0) == 1.0

    def test_trivial_uncovered(self):
        # CC=1: 1 * 1 + 1 = 2
        assert crap_score(1, 0.0) == 2.0


class TestSortByCrap:
    def test_sorts_descending(self):
        entries = [
            CrapEntry(name="a", module="mod", complexity=1, coverage=100.0, crap=10.0),
            CrapEntry(name="b", module="mod", complexity=1, coverage=100.0, crap=50.0),
            CrapEntry(name="c", module="mod", complexity=1, coverage=100.0, crap=1.0),
        ]
        sorted_entries = sort_by_crap(entries)
        assert [e.name for e in sorted_entries] == ["b", "a", "c"]

    def test_single_entry(self):
        entries = [CrapEntry(name="x", module="mod", complexity=1, coverage=100.0, crap=5.0)]
        assert sort_by_crap(entries) == entries

    def test_empty(self):
        assert sort_by_crap([]) == []


class TestFormatReport:
    def test_contains_function_name(self):
        entries = [CrapEntry(name="foo", module="test.bar", complexity=3, coverage=85.0, crap=4.5)]
        report = format_report(entries)
        assert "foo" in report

    def test_contains_module(self):
        entries = [CrapEntry(name="foo", module="test.bar", complexity=3, coverage=85.0, crap=4.5)]
        report = format_report(entries)
        assert "test.bar" in report

    def test_contains_crap_header(self):
        entries = [CrapEntry(name="foo", module="test.bar", complexity=3, coverage=85.0, crap=4.5)]
        report = format_report(entries)
        assert "CRAP" in report

    def test_header_present(self):
        report = format_report([])
        assert "CRAP Report" in report
        assert "Function" in report
        assert "Module" in report

    def test_multiple_entries_ordered(self):
        entries = [
            CrapEntry(name="alpha", module="mod", complexity=2, coverage=100.0, crap=2.0),
            CrapEntry(name="beta", module="mod", complexity=5, coverage=0.0, crap=30.0),
        ]
        report = format_report(entries)
        assert report.index("alpha") < report.index("beta")


class TestFormatJsonReport:
    def test_valid_json(self):
        entries = [CrapEntry(name="foo", module="mod.bar", complexity=3, coverage=85.0, crap=4.5)]
        result = format_json_report(entries)
        parsed = json.loads(result)
        assert isinstance(parsed, dict)

    def test_correct_fields(self):
        entries = [CrapEntry(name="foo", module="mod.bar", complexity=3, coverage=85.0, crap=4.5123)]
        parsed = json.loads(format_json_report(entries))
        assert parsed["tool"] == "crap4py"
        assert len(parsed["entries"]) == 1
        entry = parsed["entries"][0]
        assert entry["name"] == "foo"
        assert entry["module"] == "mod.bar"
        assert entry["complexity"] == 3
        assert entry["coverage"] == 85.0
        assert entry["crap"] == 4.5  # rounded to 1 decimal

    def test_empty_entries(self):
        parsed = json.loads(format_json_report([]))
        assert parsed["tool"] == "crap4py"
        assert parsed["entries"] == []

    def test_indent(self):
        result = format_json_report([])
        # indent=2 means multiline with spaces
        assert "\n" in result
        assert "  " in result


class TestFormatMarkdownReport:
    def test_header(self):
        report = format_markdown_report([])
        assert "# CRAP Report" in report

    def test_separator_row(self):
        report = format_markdown_report([])
        assert "|---|---|---:|---:|---:|" in report

    def test_column_headers(self):
        report = format_markdown_report([])
        assert "| Function | Module | CC | Cov% | CRAP |" in report

    def test_entry_row(self):
        entries = [CrapEntry(name="foo", module="mod.bar", complexity=3, coverage=85.0, crap=4.5)]
        report = format_markdown_report(entries)
        assert "| foo | mod.bar | 3 | 85.0% | 4.5 |" in report

    def test_multiple_entries(self):
        entries = [
            CrapEntry(name="alpha", module="mod", complexity=2, coverage=100.0, crap=2.0),
            CrapEntry(name="beta", module="mod", complexity=5, coverage=0.0, crap=30.0),
        ]
        report = format_markdown_report(entries)
        assert "alpha" in report
        assert "beta" in report


class TestFormatCsvReport:
    def test_header_row(self):
        result = format_csv_report([])
        lines = result.strip().split("\n")
        assert lines[0] == "Function,Module,CC,Coverage,CRAP"

    def test_data_row(self):
        entries = [CrapEntry(name="foo", module="mod.bar", complexity=3, coverage=85.0, crap=4.5)]
        result = format_csv_report(entries)
        lines = result.strip().split("\n")
        assert lines[1] == "foo,mod.bar,3,85.0,4.5"

    def test_trailing_newline(self):
        result = format_csv_report([])
        assert result.endswith("\n")

    def test_comma_quoting(self):
        entries = [CrapEntry(name="foo,bar", module="mod", complexity=1, coverage=100.0, crap=1.0)]
        result = format_csv_report(entries)
        lines = result.strip().split("\n")
        # Field with comma should be quoted
        assert '"foo,bar"' in lines[1]

    def test_multiple_rows(self):
        entries = [
            CrapEntry(name="a", module="mod", complexity=1, coverage=100.0, crap=1.0),
            CrapEntry(name="b", module="mod", complexity=2, coverage=50.0, crap=5.0),
        ]
        result = format_csv_report(entries)
        lines = result.strip().split("\n")
        assert len(lines) == 3  # header + 2 data rows

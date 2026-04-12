import pytest
from crap4py.core import analyze_file, build_entries, filter_sources, find_source_files, find_source_files_with_options
from crap4py.models import CrapEntry, FunctionInfo


class TestFilterSources:
    def test_no_filter_returns_all(self):
        files = ["src/foo/combat.py", "src/foo/config.py"]
        assert filter_sources(files, []) == files

    def test_filters_to_matching(self):
        files = ["src/foo/combat.py", "src/foo/config.py", "src/foo/bar/army.py"]
        assert filter_sources(files, ["combat"]) == ["src/foo/combat.py"]

    def test_matches_nested_path(self):
        files = ["src/foo/combat.py", "src/foo/bar/army.py"]
        assert filter_sources(files, ["bar/army"]) == ["src/foo/bar/army.py"]

    def test_multiple_filters(self):
        files = ["src/foo/combat.py", "src/foo/config.py", "src/foo/army.py"]
        result = filter_sources(files, ["combat", "army"])
        assert result == ["src/foo/combat.py", "src/foo/army.py"]


class TestBuildEntries:
    def test_basic(self):
        fns = [FunctionInfo(name="foo", start_line=1, end_line=3, complexity=2)]
        file_data = {"executed_lines": [1, 2], "missing_lines": [3]}
        entries = build_entries(fns, file_data, "test.module")
        assert len(entries) == 1
        assert isinstance(entries[0], CrapEntry)
        assert entries[0].name == "foo"
        assert entries[0].module == "test.module"
        assert entries[0].complexity == 2
        assert isinstance(entries[0].coverage, float)
        assert isinstance(entries[0].crap, float)

    def test_coverage_computed(self):
        fns = [FunctionInfo(name="bar", start_line=1, end_line=2, complexity=1)]
        file_data = {"executed_lines": [1, 2], "missing_lines": []}
        entries = build_entries(fns, file_data, "mod")
        assert entries[0].coverage == 100.0
        assert entries[0].crap == 1.0

    def test_zero_coverage(self):
        fns = [FunctionInfo(name="baz", start_line=1, end_line=2, complexity=2)]
        file_data = {"executed_lines": [], "missing_lines": [1, 2]}
        entries = build_entries(fns, file_data, "mod")
        assert entries[0].coverage == 0.0
        # crap = 4 * 1 + 2 = 6
        assert entries[0].crap == 6.0

    def test_empty_fns(self):
        assert build_entries([], {}, "mod") == []


class TestFindSourceFiles:
    def test_finds_py_files_under_src(self):
        files = find_source_files()
        assert len(files) > 0
        assert all(f.endswith(".py") for f in files)
        assert all(f.startswith("src/") for f in files)

    def test_sorted(self):
        files = find_source_files()
        assert files == sorted(files)

    def test_custom_source_dir(self, tmp_path, monkeypatch):
        lib_dir = tmp_path / "lib" / "pkg"
        lib_dir.mkdir(parents=True)
        (lib_dir / "mod.py").write_text("x = 1\n")
        monkeypatch.chdir(tmp_path)
        files = find_source_files(source_dir="lib")
        assert len(files) == 1
        assert files[0] == "lib/pkg/mod.py"


class TestAnalyzeFile:
    def test_analyzes_real_file(self, tmp_path):
        src = tmp_path / "sample.py"
        src.write_text("def foo(x):\n    if x:\n        return 1\n    return 0\n")
        # Symlink or write to a src/ relative path isn't needed — just test analyze_file directly
        files_data = {
            str(src): {"executed_lines": [1, 2, 3], "missing_lines": [4]}
        }
        # analyze_file opens the file directly so we can use absolute path
        entries = analyze_file(str(src), files_data)
        assert len(entries) == 1
        assert isinstance(entries[0], CrapEntry)
        assert entries[0].name == "foo"
        assert entries[0].complexity == 2
        assert isinstance(entries[0].coverage, float)
        assert isinstance(entries[0].crap, float)

    def test_missing_coverage_data(self, tmp_path):
        src = tmp_path / "sample.py"
        src.write_text("def bar(x):\n    return x\n")
        entries = analyze_file(str(src), {})
        assert len(entries) == 1
        assert entries[0].coverage == 100.0

    def test_full_pipeline_on_own_source(self):
        """Integration: analyze a real crap4py source file."""
        entries = analyze_file("src/crap4py/complexity.py", {})
        assert len(entries) > 0
        for e in entries:
            assert isinstance(e, CrapEntry)
            assert isinstance(e.name, str)
            assert isinstance(e.module, str)
            assert isinstance(e.complexity, int)
            assert 0 <= e.coverage <= 100
            assert e.crap > 0

    def test_analyze_file_syntax_error_returns_empty(self, tmp_path):
        src = tmp_path / "bad.py"
        src.write_text("def foo(\n")
        with pytest.warns(UserWarning, match="Skipping"):
            entries = analyze_file(str(src), {})
        assert entries == []

    def test_analyze_file_custom_source_dir(self, tmp_path):
        lib_dir = tmp_path / "lib" / "pkg"
        lib_dir.mkdir(parents=True)
        src = lib_dir / "mod.py"
        src.write_text("def hello():\n    return 1\n")
        source_path = str(tmp_path / "lib" / "pkg" / "mod.py")
        entries = analyze_file(source_path, {}, source_dir=str(tmp_path / "lib"))
        assert len(entries) == 1
        assert entries[0].module == "pkg.mod"


class TestFindSourceFilesWithOptions:
    def test_excludes_pattern(self, tmp_path, monkeypatch):
        pkg = tmp_path / "src" / "pkg"
        pkg.mkdir(parents=True)
        (pkg / "keep.py").write_text("x = 1\n")
        (pkg / "test_skip.py").write_text("x = 2\n")
        monkeypatch.chdir(tmp_path)
        result = find_source_files_with_options(src_dirs=["src"], excludes=["test_skip"])
        assert len(result) == 1
        assert "keep.py" in result[0]
        assert all("test_skip" not in f for f in result)

    def test_multiple_excludes(self, tmp_path, monkeypatch):
        pkg = tmp_path / "src" / "pkg"
        pkg.mkdir(parents=True)
        (pkg / "keep.py").write_text("x = 1\n")
        (pkg / "skip_a.py").write_text("x = 2\n")
        (pkg / "skip_b.py").write_text("x = 3\n")
        monkeypatch.chdir(tmp_path)
        result = find_source_files_with_options(src_dirs=["src"], excludes=["skip_a", "skip_b"])
        assert len(result) == 1
        assert "keep.py" in result[0]

    def test_multiple_src_dirs(self, tmp_path, monkeypatch):
        dir_a = tmp_path / "src_a" / "pkg"
        dir_b = tmp_path / "src_b" / "pkg"
        dir_a.mkdir(parents=True)
        dir_b.mkdir(parents=True)
        (dir_a / "a.py").write_text("x = 1\n")
        (dir_b / "b.py").write_text("x = 2\n")
        monkeypatch.chdir(tmp_path)
        result = find_source_files_with_options(src_dirs=["src_a", "src_b"], excludes=[])
        assert len(result) == 2
        paths_str = " ".join(result)
        assert "a.py" in paths_str
        assert "b.py" in paths_str

    def test_deduplicates(self, tmp_path, monkeypatch):
        pkg = tmp_path / "src" / "pkg"
        pkg.mkdir(parents=True)
        (pkg / "mod.py").write_text("x = 1\n")
        monkeypatch.chdir(tmp_path)
        result = find_source_files_with_options(src_dirs=["src", "src"], excludes=[])
        assert len(result) == 1

    def test_sorted_output(self, tmp_path, monkeypatch):
        pkg = tmp_path / "src" / "pkg"
        pkg.mkdir(parents=True)
        (pkg / "z_last.py").write_text("x = 1\n")
        (pkg / "a_first.py").write_text("x = 2\n")
        (pkg / "m_middle.py").write_text("x = 3\n")
        monkeypatch.chdir(tmp_path)
        result = find_source_files_with_options(src_dirs=["src"], excludes=[])
        assert result == sorted(result)

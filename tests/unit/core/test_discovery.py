"""Tests for test discovery: file finding, module loading, and case extraction."""

from __future__ import annotations

from pathlib import Path

import pytest

from agentprobe.core.discovery import (
    discover_test_files,
    extract_test_cases,
    load_test_module,
)


class TestDiscoverTestFiles:
    """Tests for discover_test_files()."""

    def test_returns_sorted_matching_files(self, tmp_path: Path) -> None:
        (tmp_path / "test_beta.py").write_text("# beta", encoding="utf-8")
        (tmp_path / "test_alpha.py").write_text("# alpha", encoding="utf-8")
        (tmp_path / "helper.py").write_text("# helper", encoding="utf-8")

        result = discover_test_files(tmp_path)

        assert len(result) == 2
        assert result[0].name == "test_alpha.py"
        assert result[1].name == "test_beta.py"

    def test_nonexistent_directory_returns_empty(self, tmp_path: Path) -> None:
        result = discover_test_files(tmp_path / "no_such_dir")

        assert result == []

    def test_empty_directory_returns_empty(self, tmp_path: Path) -> None:
        result = discover_test_files(tmp_path)

        assert result == []

    def test_custom_pattern(self, tmp_path: Path) -> None:
        (tmp_path / "test_foo.py").write_text("# test", encoding="utf-8")
        (tmp_path / "check_bar.py").write_text("# check", encoding="utf-8")

        result = discover_test_files(tmp_path, pattern="check_*.py")

        assert len(result) == 1
        assert result[0].name == "check_bar.py"

    def test_recursive_discovery(self, tmp_path: Path) -> None:
        sub = tmp_path / "subdir"
        sub.mkdir()
        (tmp_path / "test_root.py").write_text("# root", encoding="utf-8")
        (sub / "test_nested.py").write_text("# nested", encoding="utf-8")

        result = discover_test_files(tmp_path)

        assert len(result) == 2
        names = {p.name for p in result}
        assert names == {"test_root.py", "test_nested.py"}

    def test_accepts_string_path(self, tmp_path: Path) -> None:
        (tmp_path / "test_a.py").write_text("# a", encoding="utf-8")

        result = discover_test_files(str(tmp_path))

        assert len(result) == 1

    def test_ignores_non_matching_files(self, tmp_path: Path) -> None:
        (tmp_path / "my_module.py").write_text("# module", encoding="utf-8")
        (tmp_path / "README.md").write_text("# readme", encoding="utf-8")

        result = discover_test_files(tmp_path)

        assert result == []


class TestLoadTestModule:
    """Tests for load_test_module()."""

    def test_loads_valid_module(self, tmp_path: Path) -> None:
        test_file = tmp_path / "test_sample.py"
        test_file.write_text("VALUE = 42\n", encoding="utf-8")

        module_name = load_test_module(test_file)

        assert "test_sample" in module_name
        assert module_name.startswith("agentprobe_tests.")

    def test_invalid_syntax_raises_import_error(self, tmp_path: Path) -> None:
        test_file = tmp_path / "test_bad.py"
        test_file.write_text("def broken(\n", encoding="utf-8")

        with pytest.raises(ImportError, match="Failed to load"):
            load_test_module(test_file)

    def test_missing_file_raises_import_error(self, tmp_path: Path) -> None:
        test_file = tmp_path / "test_missing.py"

        with pytest.raises(ImportError):
            load_test_module(test_file)

    def test_module_with_import_error_raises(self, tmp_path: Path) -> None:
        test_file = tmp_path / "test_import_err.py"
        test_file.write_text("import nonexistent_module_xyz_12345\n", encoding="utf-8")

        with pytest.raises(ImportError, match="Failed to load"):
            load_test_module(test_file)

    def test_unique_module_names_per_file(self, tmp_path: Path) -> None:
        file_a = tmp_path / "test_a.py"
        file_b = tmp_path / "test_b.py"
        file_a.write_text("A = 1\n", encoding="utf-8")
        file_b.write_text("B = 2\n", encoding="utf-8")

        name_a = load_test_module(file_a)
        name_b = load_test_module(file_b)

        assert name_a != name_b


class TestExtractTestCases:
    """Tests for extract_test_cases()."""

    def test_empty_directory_returns_empty(self, tmp_path: Path) -> None:
        result = extract_test_cases(tmp_path)

        assert result == []

    def test_extracts_scenarios_from_test_files(self, tmp_path: Path) -> None:
        test_file = tmp_path / "test_scenarios.py"
        test_file.write_text(
            "from agentprobe.core.scenario import scenario\n"
            "\n"
            '@scenario(name="hello_test", input_text="Hi there")\n'
            "def test_hello():\n"
            "    pass\n",
            encoding="utf-8",
        )

        result = extract_test_cases(tmp_path)

        assert len(result) == 1
        assert result[0].name == "hello_test"
        assert result[0].input_text == "Hi there"

    def test_skips_unloadable_files(self, tmp_path: Path) -> None:
        good_file = tmp_path / "test_good.py"
        good_file.write_text(
            "from agentprobe.core.scenario import scenario\n"
            "\n"
            '@scenario(name="good_test", input_text="test")\n'
            "def test_good():\n"
            "    pass\n",
            encoding="utf-8",
        )
        bad_file = tmp_path / "test_bad.py"
        bad_file.write_text("import nonexistent_xyz_999\n", encoding="utf-8")

        result = extract_test_cases(tmp_path)

        assert len(result) == 1
        assert result[0].name == "good_test"

    def test_custom_pattern(self, tmp_path: Path) -> None:
        test_file = tmp_path / "check_agent.py"
        test_file.write_text(
            "from agentprobe.core.scenario import scenario\n"
            "\n"
            '@scenario(name="custom_test", input_text="test")\n'
            "def test_custom():\n"
            "    pass\n",
            encoding="utf-8",
        )

        result = extract_test_cases(tmp_path, pattern="check_*.py")

        assert len(result) == 1
        assert result[0].name == "custom_test"

    def test_multiple_scenarios_in_one_file(self, tmp_path: Path) -> None:
        test_file = tmp_path / "test_multi.py"
        test_file.write_text(
            "from agentprobe.core.scenario import scenario\n"
            "\n"
            '@scenario(name="test_one", input_text="first")\n'
            "def test_one():\n"
            "    pass\n"
            "\n"
            '@scenario(name="test_two", input_text="second")\n'
            "def test_two():\n"
            "    pass\n",
            encoding="utf-8",
        )

        result = extract_test_cases(tmp_path)

        assert len(result) == 2
        names = {tc.name for tc in result}
        assert names == {"test_one", "test_two"}

    def test_files_without_scenarios_return_empty(self, tmp_path: Path) -> None:
        test_file = tmp_path / "test_plain.py"
        test_file.write_text("x = 1\n", encoding="utf-8")

        result = extract_test_cases(tmp_path)

        assert result == []

    def test_nonexistent_directory_returns_empty(self, tmp_path: Path) -> None:
        result = extract_test_cases(tmp_path / "no_such_dir")

        assert result == []

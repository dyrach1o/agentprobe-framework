"""Tests for the CLI test command."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from agentprobe.cli.main import cli


class TestTestCommand:
    """Tests for the ``agentprobe test`` CLI command."""

    def test_help(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["test", "--help"])

        assert result.exit_code == 0
        assert "test" in result.output.lower()

    def test_no_tests_in_empty_dir(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["test", "-d", str(tmp_path)])

        assert result.exit_code == 0
        assert "No test cases" in result.output

    def test_discovers_scenarios(self, tmp_path: Path) -> None:
        test_file = tmp_path / "test_demo.py"
        test_file.write_text(
            "from agentprobe.core.scenario import scenario\n"
            "\n"
            '@scenario(name="demo_test", input_text="hello")\n'
            "def test_demo():\n"
            "    pass\n",
            encoding="utf-8",
        )
        runner = CliRunner()
        result = runner.invoke(cli, ["test", "-d", str(tmp_path)])

        assert result.exit_code == 0
        assert "1 test case" in result.output
        assert "demo_test" in result.output

    def test_discovers_multiple_scenarios(self, tmp_path: Path) -> None:
        test_file = tmp_path / "test_multi.py"
        test_file.write_text(
            "from agentprobe.core.scenario import scenario\n"
            "\n"
            '@scenario(name="test_a", input_text="a")\n'
            "def test_a():\n"
            "    pass\n"
            "\n"
            '@scenario(name="test_b", input_text="b", tags=["fast"])\n'
            "def test_b():\n"
            "    pass\n",
            encoding="utf-8",
        )
        runner = CliRunner()
        result = runner.invoke(cli, ["test", "-d", str(tmp_path)])

        assert result.exit_code == 0
        assert "2 test case" in result.output
        assert "test_a" in result.output
        assert "test_b" in result.output
        assert "fast" in result.output

    def test_custom_pattern(self, tmp_path: Path) -> None:
        test_file = tmp_path / "check_agent.py"
        test_file.write_text(
            "from agentprobe.core.scenario import scenario\n"
            "\n"
            '@scenario(name="check_test", input_text="check")\n'
            "def test_check():\n"
            "    pass\n",
            encoding="utf-8",
        )
        runner = CliRunner()
        result = runner.invoke(cli, ["test", "-d", str(tmp_path), "-p", "check_*.py"])

        assert result.exit_code == 0
        assert "check_test" in result.output

    def test_with_config_file(self, tmp_path: Path) -> None:
        config_file = tmp_path / "agentprobe.yaml"
        test_dir = tmp_path / "my_tests"
        test_dir.mkdir()
        config_file.write_text(
            f"test_dir: {test_dir}\n",
            encoding="utf-8",
        )
        runner = CliRunner()
        result = runner.invoke(cli, ["test", "-c", str(config_file)])

        assert result.exit_code == 0
        assert "No test cases" in result.output

    def test_test_dir_overrides_config(self, tmp_path: Path) -> None:
        config_file = tmp_path / "agentprobe.yaml"
        config_file.write_text("test_dir: nonexistent\n", encoding="utf-8")
        test_dir = tmp_path / "real_tests"
        test_dir.mkdir()
        runner = CliRunner()
        result = runner.invoke(cli, ["test", "-c", str(config_file), "-d", str(test_dir)])

        assert result.exit_code == 0
        assert "No test cases" in result.output

    def test_tags_displayed_as_none(self, tmp_path: Path) -> None:
        test_file = tmp_path / "test_notags.py"
        test_file.write_text(
            "from agentprobe.core.scenario import scenario\n"
            "\n"
            '@scenario(name="no_tags_test", input_text="test")\n'
            "def test_no_tags():\n"
            "    pass\n",
            encoding="utf-8",
        )
        runner = CliRunner()
        result = runner.invoke(cli, ["test", "-d", str(tmp_path)])

        assert result.exit_code == 0
        assert "tags: none" in result.output

    def test_parallel_flag(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["test", "-d", str(tmp_path), "--parallel"])

        assert result.exit_code == 0

    def test_sequential_flag(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["test", "-d", str(tmp_path), "--sequential"])

        assert result.exit_code == 0

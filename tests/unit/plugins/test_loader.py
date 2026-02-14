"""Tests for the plugin loader."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from agentprobe.core.exceptions import PluginError
from agentprobe.core.models import PluginType
from agentprobe.plugins.base import PluginBase
from agentprobe.plugins.loader import PluginLoader


class _TestPlugin(PluginBase):
    @property
    def name(self) -> str:
        return "test-loaded"

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.EVALUATOR


class TestLoadFromClass:
    """Test loading plugins from direct class references."""

    def test_load_valid_class(self) -> None:
        loader = PluginLoader()
        plugin = loader.load_from_class(_TestPlugin)
        assert plugin.name == "test-loaded"

    def test_non_plugin_class_raises(self) -> None:
        loader = PluginLoader()
        with pytest.raises(PluginError, match="not a PluginBase"):
            loader.load_from_class(str)  # type: ignore[arg-type]

    def test_not_a_type_raises(self) -> None:
        loader = PluginLoader()
        with pytest.raises(PluginError, match="not a PluginBase"):
            loader.load_from_class("not a class")  # type: ignore[arg-type]


class TestLoadFromPath:
    """Test loading plugins from file paths."""

    def test_load_valid_file(self, tmp_path: Path) -> None:
        plugin_file = tmp_path / "my_plugin.py"
        plugin_file.write_text(
            "from agentprobe.plugins.base import PluginBase\n"
            "from agentprobe.core.models import PluginType\n"
            "\n"
            "class MyPlugin(PluginBase):\n"
            "    @property\n"
            "    def name(self) -> str:\n"
            '        return "my-file-plugin"\n'
            "    @property\n"
            "    def plugin_type(self) -> PluginType:\n"
            "        return PluginType.EVALUATOR\n",
            encoding="utf-8",
        )
        loader = PluginLoader()
        plugin = loader.load_from_path(plugin_file)
        assert plugin.name == "my-file-plugin"

    def test_nonexistent_file_raises(self, tmp_path: Path) -> None:
        loader = PluginLoader()
        with pytest.raises(PluginError, match="not found"):
            loader.load_from_path(tmp_path / "nonexistent.py")

    def test_non_py_file_raises(self, tmp_path: Path) -> None:
        txt_file = tmp_path / "plugin.txt"
        txt_file.write_text("not python")
        loader = PluginLoader()
        with pytest.raises(PluginError, match=r"\.py file"):
            loader.load_from_path(txt_file)

    def test_no_plugin_class_raises(self, tmp_path: Path) -> None:
        plugin_file = tmp_path / "empty_plugin.py"
        plugin_file.write_text("x = 42\n", encoding="utf-8")
        loader = PluginLoader()
        with pytest.raises(PluginError, match="No PluginBase subclass"):
            loader.load_from_path(plugin_file)

    def test_syntax_error_raises(self, tmp_path: Path) -> None:
        plugin_file = tmp_path / "bad_plugin.py"
        plugin_file.write_text("def broken(:\n", encoding="utf-8")
        loader = PluginLoader()
        with pytest.raises(PluginError, match="Failed to load"):
            loader.load_from_path(plugin_file)


class TestLoadFromEntryPoints:
    """Test loading plugins from entry points."""

    def test_empty_entry_points(self) -> None:
        loader = PluginLoader(entry_point_group="nonexistent.group")
        plugins = loader.load_from_entry_points()
        assert plugins == []

    def test_entry_point_with_valid_plugin(self) -> None:
        mock_ep = MagicMock()
        mock_ep.name = "test-ep"
        mock_ep.load.return_value = _TestPlugin

        mock_eps = MagicMock()
        mock_eps.select.return_value = [mock_ep]

        loader = PluginLoader()
        with patch(
            "agentprobe.plugins.loader.importlib.metadata.entry_points", return_value=mock_eps
        ):
            plugins = loader.load_from_entry_points()

        assert len(plugins) == 1
        assert plugins[0].name == "test-loaded"

    def test_entry_point_load_failure_skipped(self) -> None:
        mock_ep = MagicMock()
        mock_ep.name = "bad-ep"
        mock_ep.load.side_effect = ImportError("module not found")

        mock_eps = MagicMock()
        mock_eps.select.return_value = [mock_ep]

        loader = PluginLoader()
        with patch(
            "agentprobe.plugins.loader.importlib.metadata.entry_points", return_value=mock_eps
        ):
            plugins = loader.load_from_entry_points()

        assert plugins == []


class TestLoadAll:
    """Test load_all combining entry points and directories."""

    def test_load_from_directory(self, tmp_path: Path) -> None:
        plugin_file = tmp_path / "dir_plugin.py"
        plugin_file.write_text(
            "from agentprobe.plugins.base import PluginBase\n"
            "from agentprobe.core.models import PluginType\n"
            "\n"
            "class DirPlugin(PluginBase):\n"
            "    @property\n"
            "    def name(self) -> str:\n"
            '        return "dir-plugin"\n'
            "    @property\n"
            "    def plugin_type(self) -> PluginType:\n"
            "        return PluginType.EVALUATOR\n",
            encoding="utf-8",
        )
        loader = PluginLoader(entry_point_group="nonexistent.group")
        plugins = loader.load_all(directories=[str(tmp_path)])
        assert len(plugins) == 1
        assert plugins[0].name == "dir-plugin"

    def test_skips_underscore_files(self, tmp_path: Path) -> None:
        (tmp_path / "__init__.py").write_text("", encoding="utf-8")
        (tmp_path / "_private.py").write_text("x = 1", encoding="utf-8")
        loader = PluginLoader(entry_point_group="nonexistent.group")
        plugins = loader.load_all(directories=[str(tmp_path)])
        assert plugins == []

    def test_nonexistent_directory_skipped(self) -> None:
        loader = PluginLoader(entry_point_group="nonexistent.group")
        plugins = loader.load_all(directories=["/nonexistent/path"])
        assert plugins == []

    def test_empty_directories_list(self) -> None:
        loader = PluginLoader(entry_point_group="nonexistent.group")
        plugins = loader.load_all(directories=[])
        assert plugins == []

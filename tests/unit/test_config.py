import json
import platform
from pathlib import Path

import pytest

from file_explorer.config import (
    AppConfig,
    ConfigManager,
    KNOWN_KEYS,
    default_config_path,
    load_config,
    save_config,
)


class TestAppConfig:

    def test_default_values(self):
        config = AppConfig()
        assert config.start_directory == "~"
        assert config.show_hidden_files is False
        assert config.default_conflict_strategy == "rename"
        assert config.max_history == 50
        assert config.max_search_results == 1000
        assert config.log_level == "INFO"
        assert config.language == "en"
        assert config.theme == "system"

    def test_custom_values(self):
        config = AppConfig(
            start_directory="/custom",
            show_hidden_files=True,
            default_conflict_strategy="overwrite",
            max_history=100,
            max_search_results=500,
            log_level="DEBUG",
            language="de",
            theme="dark",
        )
        assert config.start_directory == "/custom"
        assert config.show_hidden_files is True
        assert config.default_conflict_strategy == "overwrite"
        assert config.max_history == 100
        assert config.max_search_results == 500
        assert config.log_level == "DEBUG"
        assert config.language == "de"
        assert config.theme == "dark"


class TestDefaultConfigPath:

    def test_returns_path(self):
        path = default_config_path()
        assert isinstance(path, Path)
        assert path.name == "config.json"

    def test_platform_specific_parent(self, monkeypatch):
        monkeypatch.setattr(platform, "system", lambda: "Windows")
        monkeypatch.setenv("APPDATA", r"C:\Users\Test\AppData\Roaming")
        path = default_config_path()
        assert str(path).startswith(r"C:\Users\Test\AppData\Roaming")

    def test_linux_path(self, monkeypatch):
        monkeypatch.setattr(platform, "system", lambda: "Linux")
        path = default_config_path()
        parts = path.parts
        assert ".config" in parts
        assert "file_explorer" in parts
        assert path.name == "config.json"

    def test_macos_path(self, monkeypatch):
        monkeypatch.setattr(platform, "system", lambda: "Darwin")
        path = default_config_path()
        assert "Application Support" in str(path)
        assert "Library" in str(path)


class TestLoadConfig:

    def test_load_defaults_when_missing(self, tmp_path: Path):
        missing = tmp_path / "nonexistent" / "config.json"
        config = load_config(missing)
        assert isinstance(config, AppConfig)
        assert config.start_directory == "~"

    def test_load_custom_values(self, tmp_path: Path):
        config_file = tmp_path / "config.json"
        data = {
            "start_directory": "/test",
            "show_hidden_files": True,
            "max_history": 99,
        }
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(json.dumps(data), encoding="utf-8")
        config = load_config(config_file)
        assert config.start_directory == "/test"
        assert config.show_hidden_files is True
        assert config.max_history == 99
        assert config.default_conflict_strategy == "rename"

    def test_load_ignores_unknown_keys(self, tmp_path: Path):
        config_file = tmp_path / "config.json"
        data = {"start_directory": "/ok", "unknown_key": 42, "another_unknown": True}
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(json.dumps(data), encoding="utf-8")
        config = load_config(config_file)
        assert config.start_directory == "/ok"

    def test_corrupted_json_falls_back_to_defaults(self, tmp_path: Path):
        config_file = tmp_path / "config.json"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text("{invalid json", encoding="utf-8")
        config = load_config(config_file)
        assert isinstance(config, AppConfig)
        assert config.start_directory == "~"

    def test_corrupted_json_backs_up_file(self, tmp_path: Path):
        config_file = tmp_path / "config.json"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text("{{{broken", encoding="utf-8")
        load_config(config_file)
        assert config_file.with_suffix(".json.corrupt").exists()

    def test_not_a_dict_returns_defaults(self, tmp_path: Path):
        config_file = tmp_path / "config.json"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text('"just a string"', encoding="utf-8")
        config = load_config(config_file)
        assert isinstance(config, AppConfig)


class TestSaveConfig:

    def test_save_creates_file(self, tmp_path: Path):
        config = AppConfig(start_directory="/saved")
        config_file = tmp_path / "config.json"
        save_config(config, config_file)
        assert config_file.exists()
        content = json.loads(config_file.read_text(encoding="utf-8"))
        assert content["start_directory"] == "/saved"

    def test_save_is_atomic(self, tmp_path: Path):
        config = AppConfig()
        config_file = tmp_path / "config.json"
        save_config(config, config_file)
        tmp_files = list(tmp_path.glob("*.tmp"))
        assert len(tmp_files) == 0

    def test_save_roundtrip(self, tmp_path: Path):
        original = AppConfig(
            start_directory="/test",
            show_hidden_files=True,
            default_conflict_strategy="skip",
            max_history=10,
            max_search_results=50,
            log_level="DEBUG",
            language="fr",
            theme="dark",
        )
        config_file = tmp_path / "config.json"
        save_config(original, config_file)
        loaded = load_config(config_file)
        for key in KNOWN_KEYS:
            assert getattr(loaded, key) == getattr(original, key), f"Mismatch for {key}"

    def test_save_with_non_existent_dir_creates_parents(self, tmp_path: Path):
        config = AppConfig()
        nested = tmp_path / "a" / "b" / "c" / "config.json"
        save_config(config, nested)
        assert nested.exists()

    def test_save_uses_indentation(self, tmp_path: Path):
        config = AppConfig()
        config_file = tmp_path / "config.json"
        save_config(config, config_file)
        content = config_file.read_text(encoding="utf-8")
        assert '  "start_directory"' in content


class TestConfigManager:

    def test_get_returns_value(self, tmp_path: Path):
        mgr = ConfigManager(tmp_path / "config.json")
        assert mgr.get("start_directory") == "~"

    def test_get_unknown_key_raises(self, tmp_path: Path):
        mgr = ConfigManager(tmp_path / "config.json")
        with pytest.raises(KeyError):
            mgr.get("nonexistent_key")

    def test_set_updates_value(self, tmp_path: Path):
        config_file = tmp_path / "config.json"
        mgr = ConfigManager(config_file)
        mgr.set("max_history", 200)
        assert mgr.get("max_history") == 200
        assert config_file.exists()

    def test_set_persists_to_disk(self, tmp_path: Path):
        config_file = tmp_path / "config.json"
        mgr = ConfigManager(config_file)
        mgr.set("language", "ja")
        loaded = load_config(config_file)
        assert loaded.language == "ja"

    def test_set_unknown_key_raises(self, tmp_path: Path):
        mgr = ConfigManager(tmp_path / "config.json")
        with pytest.raises(KeyError):
            mgr.set("bad_key", 123)

    def test_reset_to_defaults(self, tmp_path: Path):
        config_file = tmp_path / "config.json"
        mgr = ConfigManager(config_file)
        mgr.set("max_history", 999)
        mgr.reset_to_defaults()
        assert mgr.get("max_history") == 50

    def test_reset_to_defaults_persists(self, tmp_path: Path):
        config_file = tmp_path / "config.json"
        mgr = ConfigManager(config_file)
        mgr.set("log_level", "ERROR")
        mgr.reset_to_defaults()
        loaded = load_config(config_file)
        assert loaded.log_level == "INFO"

    def test_path_property(self, tmp_path: Path):
        expected = tmp_path / "my_config.json"
        mgr = ConfigManager(expected)
        assert mgr.path == expected

    def test_reload_discards_changes(self, tmp_path: Path):
        config_file = tmp_path / "config.json"
        save_config(AppConfig(max_history=77), config_file)
        mgr = ConfigManager(config_file)
        assert mgr.get("max_history") == 77
        mgr.set("max_history", 99)
        save_config(AppConfig(max_history=88), config_file)
        mgr.reload()
        assert mgr.get("max_history") == 88

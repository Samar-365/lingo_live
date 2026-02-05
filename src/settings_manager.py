import json
import os
import platform

class SettingsManager:
    """Manages persistent application settings."""
    
    def __init__(self):
        self.settings_file = "settings.json"
        self.default_settings = {
            "hotkey": "ctrl+alt+t",
            "opacity": 1.0,
            "theme": "Dark",
            "font_family": "Segoe UI",
            "font_size": 14
        }
        self.settings = self._load_settings()

    def _load_settings(self):
        """Load settings from JSON file or return defaults."""
        if not os.path.exists(self.settings_file):
            return self.default_settings.copy()
        
        try:
            with open(self.settings_file, 'r') as f:
                loaded = json.load(f)
                # Merge with defaults to ensure all keys exist
                settings = self.default_settings.copy()
                settings.update(loaded)
                return settings
        except Exception as e:
            print(f"[Settings] Error loading: {e}")
            return self.default_settings.copy()

    def save_settings(self):
        """Save current settings to JSON file."""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
            print("[Settings] Saved successfully.")
        except Exception as e:
            print(f"[Settings] Error saving: {e}")

    def get(self, key, default=None):
        """Get a setting value."""
        return self.settings.get(key, default)

    def set(self, key, value):
        """Set a setting value and save."""
        self.settings[key] = value
        self.save_settings()

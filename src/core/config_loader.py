import os
import json
from typing import Optional
from src.core.types import RepoRunnerConfig

class ConfigLoader:
    """
    Locates and parses repo-runner.json project configuration files.
    """
    
    CONFIG_FILENAME = "repo-runner.json"

    @staticmethod
    def load_config(repo_root: str) -> RepoRunnerConfig:
        """
        Attempts to load the configuration from the target repository root.
        Returns a default RepoRunnerConfig if no file exists or if parsing fails.
        """
        config_path = os.path.join(repo_root, ConfigLoader.CONFIG_FILENAME)
        
        if not os.path.exists(config_path):
            return RepoRunnerConfig()
            
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return RepoRunnerConfig.model_validate(data)
        except json.JSONDecodeError as e:
            print(f"Warning: Invalid JSON in {config_path}. Using default configuration. Error: {e}")
            return RepoRunnerConfig()
        except Exception as e:
            print(f"Warning: Failed to load {config_path}. Using default configuration. Error: {e}")
            return RepoRunnerConfig()
import os
import yaml

def get_config_path():
    """Returns the absolute path to config.yaml regardless of execution directory."""
    # Start from current file's directory
    # Move up one level to the project root
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, 'config.yaml')
    
    # Debug print for CI/CD visibility
    print(f"DEBUG: Looking for config at: {config_path}")
    print(f"DEBUG: Root dir exists: {os.path.exists(base_dir)}")
    print(f"DEBUG: Config exists: {os.path.exists(config_path)}")
    
    return config_path

def load_config():
    """Loads the configuration from config.yaml."""
    config_path = get_config_path()
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.load(f, Loader=yaml.SafeLoader)

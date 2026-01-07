import yaml
import os

def load_prompt_template(filename: str) -> dict:
    """
    Load prompt template from yaml file
    """
    # Assuming prompts are in backend/prompts/
    base_path = os.path.dirname(os.path.dirname(__file__))
    path = os.path.join(base_path, "prompts", filename)
    
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def format_prompt(template: str, **kwargs) -> str:
    """
    Format prompt string with variables
    """
    return template.format(**kwargs)

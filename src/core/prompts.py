from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Tuple
from jinja2 import Environment, FileSystemLoader, StrictUndefined

DELIM = "\n---\nPrompt:\n"

@dataclass
class RenderedPrompt:
    system: str
    user: str
    expected_answer: str | None = None

def render_user_prompt(template_path: str, variables: Dict[str, Any] | None = None) -> str:
    variables = variables or {}
    env = Environment(
        loader=FileSystemLoader(str(Path(template_path).parent)),
        undefined=StrictUndefined,
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template(Path(template_path).name)
    return template.render(**variables)

def parse_expected_and_prompt(text: str) -> Tuple[str | None, str]:
    """
    Expected simple structure:
    'Expected Answer: <answer>\n---\nPrompt:\n<actual prompt>'
    """
    # Split once on the delimiter to keep parsing simple and robust
    if DELIM in text:
        header, body = text.split(DELIM, 1)
        header = header.strip()
        body = body.strip()
        # Parse 'Expected Answer: ...' line
        prefix = "Expected Answer:"
        if header.startswith(prefix):
            exp = header[len(prefix):].strip()
            return exp, body
    # Fallback: no expected header found
    return None, text.strip()

def load_text(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")

def render_prompts(system_path: str, user_template: str, variables: Dict[str, Any] | None = None) -> RenderedPrompt:
    system = load_text(system_path) if system_path else ""
    user_raw = render_user_prompt(user_template, variables or {})
    expected, user = parse_expected_and_prompt(user_raw)
    return RenderedPrompt(system=system, user=user, expected_answer=expected)

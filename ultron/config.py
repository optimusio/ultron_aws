import base64
import json
from pathlib import Path
from typing import Any, Dict

CONFIG_PATH = Path(__file__).resolve().parent.parent / 'ultron_config.json'

def load_config(path: Path = CONFIG_PATH) -> Dict[str, Any]:
    """Load and decode the encrypted JSON configuration.

    The configuration file is expected to contain base64 encoded JSON. This
    function reads the file, decodes it and returns the resulting dictionary.
    """
    data = path.read_text().strip()
    if not data:
        return {}
    decoded = base64.b64decode(data)
    return json.loads(decoded)

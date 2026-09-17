"""Config centralizado de BrainHub."""
from pathlib import Path
import json

_RAIZ = Path(__file__).parent
_cache = None

def load(path=None):
    global _cache
    if _cache is not None:
        return _cache
    p = path or _RAIZ / "brainhub_config.json"
    with open(p) as f:
        _cache = json.load(f)
    return _cache

def get(key, default=None):
    cfg = load()
    for k in key.split("."):
        if isinstance(cfg, dict):
            cfg = cfg.get(k)
        else:
            return default
        if cfg is None:
            return default
    return cfg

def reload():
    global _cache
    _cache = None
    return load()

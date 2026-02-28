import os
import json

result = {
    "openai_importable": False,
    "openai_version": None,
    "OPENAI_API_KEY_present": False,
    "OPENAI_APIKEY_present": False,
    "llm_OPENAI_AVAILABLE": None,
}
try:
    import openai
    result["openai_importable"] = True
    result["openai_version"] = getattr(openai, "__version__", None)
except Exception as e:
    result["openai_importable_error"] = str(e)

result["OPENAI_API_KEY_present"] = bool(os.environ.get("OPENAI_API_KEY"))
result["OPENAI_APIKEY_present"] = bool(os.environ.get("OPENAI_APIKEY"))
try:
    # First try a normal import
    import importlib
    m = importlib.import_module('llm_file_assistant')
    result["llm_OPENAI_AVAILABLE"] = getattr(m, 'OPENAI_AVAILABLE', None)
except Exception as e:
    # If normal import fails (ModuleNotFoundError), try to load the module by file path
    try:
        import importlib.util
        import sys
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        candidate = os.path.join(repo_root, 'llm_file_assistant.py')
        if os.path.exists(candidate):
            # Ensure repo root is on sys.path so relative imports inside the module succeed
            if repo_root not in sys.path:
                sys.path.insert(0, repo_root)
            spec = importlib.util.spec_from_file_location('llm_file_assistant', candidate)
            m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(m)
            result["llm_OPENAI_AVAILABLE"] = getattr(m, 'OPENAI_AVAILABLE', None)
            result["llm_loaded_from_path"] = candidate
        else:
            result["llm_module_error"] = str(e)
    except Exception as e2:
        result["llm_module_error"] = str(e2)

print(json.dumps(result, indent=2))

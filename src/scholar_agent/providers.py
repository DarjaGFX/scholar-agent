import os

def load_providers() -> list[dict]:
    """Build the provider matrix from the environment. No literals here."""
    names = [n.strip() for n in os.environ.get("LLM_PROVIDERS", "").split(",") if n.strip()]
    providers = []
    for name in names:
        p = name.upper()
        base_url = os.environ.get(f"{p}_BASE_URL")
        models = [m.strip() for m in os.environ.get(f"{p}_MODELS", "").split(",") if m.strip()]
        if not base_url or not models:
            print(f"skipping provider '{name}': need {p}_BASE_URL and {p}_MODELS")
            continue
        providers.append({
            "name": name,
            "base_url": base_url,
            "api_key": os.environ.get(f"{p}_API_KEY"),   # None is fine for local
            "models": models,
        })
    return providers

def arms() -> list[dict]:
    """Flatten providers × models into runnable arms for the comparison."""
    return [
        {"label": f"{p['name']}:{m}", "model": m,
         "base_url": p["base_url"], "api_key": p["api_key"]}
        for p in load_providers() for m in p["models"]
    ]

def resolve_default() -> dict:
    """The provider+model callers mean when they don't specify one."""
    from dotenv import load_dotenv
    load_dotenv()                                   # no-op if already loaded
    providers = load_providers()
    if not providers:
        raise RuntimeError("no LLM providers configured — check LLM_PROVIDERS in .env")
    name  = os.environ.get("LLM_DEFAULT_PROVIDER")
    model = os.environ.get("LLM_DEFAULT_MODEL")
    prov  = next((p for p in providers if p["name"] == name), providers[0])
    return {"base_url": prov["base_url"], "api_key": prov["api_key"],
            "model": model or prov["models"][0]}

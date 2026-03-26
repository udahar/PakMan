import os
import shlex
import shutil
import subprocess
import psycopg2
import requests
from .ollama_integration import OllamaClient, OllamaHTTPError
from provider_resilience import ProviderCallError, ProviderFallbackRouter
from .scoring import _build_ollama_client

try:
    from Benchmark.backend.runner_maintenance import is_embedding_model as benchmark_is_embedding_model
except Exception:
    benchmark_is_embedding_model = None

def get_llm():
    """Get LLM callable with provider-level fallback/circuit-breaker resilience."""
    client = _build_ollama_client(raise_http_errors=True)
    fallback_url = (
        os.getenv("PROMPTFORGE_OLLAMA_LLM_FALLBACK_URL") or "http://127.0.0.1:11434"
    ).rstrip("/")
    fallback_client = None
    if fallback_url and fallback_url != client.base_url:
        fallback_client = OllamaClient(base_url=fallback_url, raise_http_errors=True)
    known_ollama_models = {m.name for m in client.list_models()}
    default_ollama_model = (
        next(iter(known_ollama_models), None)
        or os.getenv("PROMPTFORGE_OLLAMA_FALLBACK_MODEL", "qwen2.5:3b-instruct")
    )

    breaker_timeout = int(os.getenv("PROMPTFORGE_PROVIDER_BREAKER_TIMEOUT_SECONDS", "300"))
    router = ProviderFallbackRouter(timeout_seconds=breaker_timeout)

    def infer_provider(model_name: str) -> str:
        lower = str(model_name or "").lower()
        if lower.startswith("cerebras:") or "gpt-oss" in lower:
            return "cerebras"
        if lower.startswith("qwen-cli:") or lower.startswith("qwencli:"):
            return "qwen-cli"
        if lower.startswith("openai:"):
            return "openai"
        if lower.startswith(("gpt-", "o1", "o3", "o4")):
            return "openai"
        return "ollama"

    def strip_prefix(name: str, prefix: str) -> str:
        if str(name or "").lower().startswith(prefix.lower()):
            return name[len(prefix):]
        return name

    def openai_model_for(requested_model: str) -> str:
        clean = strip_prefix(requested_model, "openai:")
        if clean.startswith(("gpt-", "o1", "o3", "o4")):
            return clean
        return os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def cerebras_model_for(requested_model: str) -> str:
        clean = strip_prefix(requested_model, "cerebras:")
        if clean and clean != requested_model:
            return clean
        return os.getenv("CEREBRAS_MODEL", "gpt-oss-120b")

    def ollama_model_for(requested_model: str) -> str:
        if requested_model in known_ollama_models:
            return requested_model
        clean = strip_prefix(requested_model, "ollama:")
        if clean in known_ollama_models:
            return clean
        return default_ollama_model

    def call_ollama(prompt: str, requested_model: str) -> str:
        use_model = ollama_model_for(requested_model)
        if not use_model:
            raise ProviderCallError("ollama", None, "no_ollama_model_available")
        num_predict = int(os.getenv("PROMPTFORGE_OLLAMA_NUM_PREDICT", "256"))
        gen_options = {"num_predict": num_predict}
        try:
            response = client.generate(use_model, prompt, options=gen_options)
            if response:
                return response
            model_lower = str(use_model or "").lower()
            if ("cloud" in model_lower) or ("chat" in model_lower):
                response = client.chat(
                    model=use_model,
                    messages=[{"role": "user", "content": prompt}],
                    options=gen_options,
                )
                if response:
                    return response
            if fallback_client is not None:
                response = fallback_client.generate(use_model, prompt, options=gen_options)
                if response:
                    return response
            raise ProviderCallError("ollama", None, "empty_response")
        except OllamaHTTPError as e:
            raise ProviderCallError("ollama", e.status_code, e.message) from e
        except ProviderCallError:
            raise
        except Exception as e:
            msg = str(e)
            if "timeout" in msg.lower():
                raise ProviderCallError("ollama", None, f"timeout: {msg}") from e
            raise ProviderCallError("ollama", None, msg) from e

    def call_cerebras(prompt: str, requested_model: str) -> str:
        api_key = os.getenv("CEREBRAS_API_KEY", "").strip()
        if not api_key:
            raise ProviderCallError("cerebras", None, "missing_cerebras_api_key")

        base_url = os.getenv("CEREBRAS_BASE_URL", "https://api.cerebras.ai/v1").rstrip("/")
        payload = {
            "model": cerebras_model_for(requested_model),
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        timeout = int(os.getenv("CEREBRAS_TIMEOUT", "120"))
        try:
            r = requests.post(
                f"{base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=timeout,
            )
            if r.status_code == 429:
                raise ProviderCallError("cerebras", 429, "rate_limited")
            r.raise_for_status()
            text = r.json().get("choices", [{}])[0].get("message", {}).get("content", "")
            if not text:
                raise ProviderCallError("cerebras", None, "empty_response")
            return text
        except ProviderCallError:
            raise
        except requests.exceptions.Timeout as e:
            raise ProviderCallError("cerebras", None, f"timeout: {e}") from e
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if getattr(e, "response", None) else None
            raise ProviderCallError("cerebras", status, str(e)) from e
        except requests.exceptions.RequestException as e:
            raise ProviderCallError("cerebras", None, str(e)) from e

    def call_openai(prompt: str, requested_model: str) -> str:
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise ProviderCallError("openai", None, "missing_openai_api_key")

        base_url = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1").rstrip("/")
        payload = {
            "model": openai_model_for(requested_model),
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        }
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        timeout = int(os.getenv("OPENAI_TIMEOUT", "120"))
        try:
            r = requests.post(
                f"{base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=timeout,
            )
            if r.status_code == 429:
                raise ProviderCallError("openai", 429, "rate_limited")
            r.raise_for_status()
            text = r.json().get("choices", [{}])[0].get("message", {}).get("content", "")
            if not text:
                raise ProviderCallError("openai", None, "empty_response")
            return text
        except ProviderCallError:
            raise
        except requests.exceptions.Timeout as e:
            raise ProviderCallError("openai", None, f"timeout: {e}") from e
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if getattr(e, "response", None) else None
            raise ProviderCallError("openai", status, str(e)) from e
        except requests.exceptions.RequestException as e:
            raise ProviderCallError("openai", None, str(e)) from e

    def call_qwen_cli(prompt: str, requested_model: str) -> str:
        del requested_model
        cmd = os.getenv("QWEN_CLI_COMMAND", "qwen").strip()
        cmd_path = shutil.which(cmd) if cmd else None
        if not cmd_path:
            raise ProviderCallError("qwen-cli", None, "qwen_cli_not_found")

        args = shlex.split(os.getenv("QWEN_CLI_ARGS", ""))
        prompt_flag = os.getenv("QWEN_CLI_PROMPT_FLAG", "--prompt").strip()
        command = [cmd_path] + args
        if prompt_flag:
            command += [prompt_flag, prompt]
        else:
            command += [prompt]

        timeout = int(os.getenv("QWEN_CLI_TIMEOUT", "120"))
        try:
            res = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            if res.returncode != 0:
                err = (res.stderr or res.stdout or "").strip()
                err_lower = err.lower()
                if "429" in err_lower or "rate limit" in err_lower:
                    raise ProviderCallError("qwen-cli", 429, err or "rate_limited")
                raise ProviderCallError("qwen-cli", None, err or f"exit_{res.returncode}")
            text = (res.stdout or "").strip()
            if not text:
                raise ProviderCallError("qwen-cli", None, "empty_response")
            return text
        except ProviderCallError:
            raise
        except subprocess.TimeoutExpired as e:
            raise ProviderCallError("qwen-cli", None, f"timeout: {e}") from e
        except Exception as e:
            raise ProviderCallError("qwen-cli", None, str(e)) from e

    router.register("ollama", call_ollama)
    router.register("cerebras", call_cerebras)
    router.register("openai", call_openai)
    router.register("qwen-cli", call_qwen_cli)

    print(f"[Provider Router] Enabled vendor fallback; breaker timeout={breaker_timeout}s")

    def llm(prompt, model="qwen2.5:3b-instruct", **kwargs):
        del kwargs
        primary_provider = infer_provider(model)
        try:
            result = router.call(primary_provider, prompt, requested_model=model)
            if result.fallback_used:
                print(
                    f"[Provider Fallback] requested={primary_provider} "
                    f"served_by={result.provider} attempts={result.attempts}"
                )
            return result.response
        except ProviderCallError as e:
            print(f"[LLM Error]: {e}")
            error_msg = str(e).lower()
            if "timeout" in error_msg:
                raise
            return None

    return llm, client


def _is_embedding_model_name(model_name: str, pg_storage_ref=None) -> bool:
    if benchmark_is_embedding_model is not None:
        try:
            return bool(
                benchmark_is_embedding_model(
                    model_name,
                    get_db_fn=lambda: psycopg2.connect(pg_storage_ref.postgres_url),
                )
            )
        except Exception:
            pass

    name = str(model_name or "").lower()
    patterns = [
        "embed",
        "-embedding",
        "bge-",
        "minilm",
        "snowflake-arctic-embed",
        "mxbai-embed",
        "embeddinggemma",
        "nomic-embed",
    ]
    return any(pattern in name for pattern in patterns)


def _get_generation_models(client, pg_storage_ref=None) -> list:
    """Get generation-capable models, preferring bm_models metadata from PostgreSQL."""
    all_models = client.list_models()
    ollama_names = [m.name for m in all_models]
    ollama_set = set(ollama_names)

    if getattr(pg_storage_ref, "_cursor", None):
        try:
            pg_storage_ref._cursor.execute(
                """
                SELECT model_name, tags
                FROM bm_models
                WHERE installed = true
                  AND COALESCE(status, 'ACTIVE') NOT IN ('DELETE', 'BANNED', 'MISSING')
                ORDER BY model_name
                """
            )
            rows = pg_storage_ref._cursor.fetchall()
            db_filtered = []
            for model_name, tags in rows:
                tags_lower = {str(t).lower() for t in (tags or [])}
                if "embedding" in tags_lower:
                    continue
                if _is_embedding_model_name(model_name, pg_storage_ref):
                    continue
                model_lower = str(model_name or "").lower()
                if model_name in ollama_set:
                    db_filtered.append(model_name)
                    continue
                if (
                    "cerebras" in tags_lower
                    or "openai" in tags_lower
                    or "qwen-cli" in tags_lower
                    or "qwen_cli" in tags_lower
                    or model_lower.startswith(("cerebras:", "openai:", "qwen-cli:", "qwencli:"))
                    or model_lower.startswith(("gpt-", "o1", "o3", "o4"))
                ):
                    db_filtered.append(model_name)

            if db_filtered:
                return db_filtered
        except Exception as e:
            print(f"[Model Filter] DB metadata query failed, using local fallback: {e}")

    # Fallback when DB is unavailable: local model-name heuristics.
    return [name for name in ollama_names if not _is_embedding_model_name(name, pg_storage_ref)]


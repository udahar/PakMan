from importlib import import_module

MODULES = [
    "torch",
    "tensorflow",
    "onnx",
    "onnxruntime",
    "peft",
    "datasets",
    "accelerate",
    "safetensors",
    "dspy",
]


def main() -> int:
    failures = []
    for name in MODULES:
        try:
            import_module(name)
            print(f"{name}: OK")
        except Exception as exc:
            failures.append((name, str(exc)))
            print(f"{name}: FAIL - {exc}")
    if failures:
        print("\nFailures:")
        for name, err in failures:
            print(f"- {name}: {err}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# ollama

Local LLM serving. Models persist in the `ollama-data` volume.

Pull the required models once the stack is up:

```bash
make pull-models
```

Installs: `qwen3:8b`, `deepseek-coder`, `llama3.1:8b`, `nomic-embed-text`.

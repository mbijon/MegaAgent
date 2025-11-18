# Repository Guidelines

## Project Structure & Module Organization

Core runtime lives at the repo root: `main.py` boots the multi-agent session, `agent.py` defines agent memory/execution, `llm.py` wraps the REST calls, and `utils.py` hosts filesystem helpers. Prompting and limits are configured in `config.py`. Generated artifacts (source files, TODO/status trackers) land in `files/`, and per-agent transcripts stream to `logs/`. Older evaluation harnesses sit under `examples/<task>/` alongside any zipped datasets.

## Build, Test, and Development Commands

Use the repo's Python uv environment (`uv venv && source .venv/bin/activate`, or `uv run …`) to guarantee consistent dependency resolution, then install deps with `pip install -U chromadb requests`.

### Configuration

**Important**: Never commit real API keys. Configuration is now managed via environment variables:

- Set `OPENAI_API_KEY` environment variable with your API key
- Optionally set `OPENAI_MODEL` (defaults to `gpt-5.1`)
- Optionally set `ENABLE_WEB_SEARCH` (defaults to `true` for GPT-5 models)

Example:

```bash
export OPENAI_API_KEY='your-api-key-here'
export OPENAI_MODEL='gpt-5.1'
export ENABLE_WEB_SEARCH='true'
```

### Running

Execute the default workflow with `python main.py`; outputs appear in `files/` and `log.txt`. Scenario-specific runners such as `python examples/GSM8k/main.py` reuse the same API surface but load task-specific prompts.

### Testing

The project uses **pytest** for testing. Run all tests with:

```bash
uv run pytest
```

Run with coverage:

```bash
uv run pytest --cov=. --cov-report=term-missing
```

Tests are located in `tests/` and include:

- Configuration tests (`test_config.py`)
- LLM integration tests including web search (`test_llm.py`)
- Agent functionality tests (`test_agent.py`)
- Utility function tests (`test_utils.py`)

All external HTTP calls are mocked to prevent actual API calls during testing. The old `test.py` interactive wrapper has been replaced by the pytest suite.

## Coding Style & Naming Conventions

Follow the existing Python style: 4-space indentation, snake_case for modules/functions, CapWords for classes, and prefer f-strings for logging. Keep modules single-responsibility (communication in `llm.py`, orchestration in `agent.py`) and avoid side effects at import time. When adding files under `files/`, make names descriptive (e.g., `files/solver_strategy.py`) so agents can address them deterministically.

## Testing Guidelines

The project uses pytest for comprehensive testing. Run `uv run pytest` from the repo root to execute all tests. The test suite includes:

- **Unit tests** for core modules (config, llm, agent, utils)
- **Integration tests** for web search functionality
- **Mocked external calls** to prevent API usage during testing
- **Coverage reporting** to ensure adequate test coverage (target: 80%+)

For task-specific validation, you can still use scenario-specific runners (e.g., `python examples/MATH/test.py`) to validate benchmark logic. Always read the corresponding `logs/<agent>.log` to confirm every agent reached the `terminate` state and that TODO files were cleared before concluding the run.

### Web Search Testing

Web search functionality is tested in `tests/test_llm.py` with mocked OpenAI API responses. Tests verify:

- Web search tool is included when enabled
- Proper API request format for GPT-5 models
- Tool call handling in agent execution

## Commit & Pull Request Guidelines

Recent history favors short, imperative summaries such as `replacing the set assignment with a dictionary`. Keep subject lines under ~60 chars, group related changes per commit, and reference issues with `#123` when applicable. Pull requests should describe the scenario exercised, list commands run (`python main.py`, dataset tests, etc.), attach any relevant artifacts from `files/`, and mention follow-up risks (e.g., API quota usage). Link logs or evaluation metrics so reviewers can retrace the run.

## Configuration & Security Notes

Never commit real API keys; inject them via environment variables and have `config.py` read from `os.environ` locally. Review any new tools or filesystem write paths carefully—agents can clobber files if prompts are too broad. When sharing logs, scrub sensitive payloads while keeping enough detail for debugging.

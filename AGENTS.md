# Repository Guidelines

## Project Structure & Module Organization
Core runtime lives at the repo root: `main.py` boots the multi-agent session, `agent.py` defines agent memory/execution, `llm.py` wraps the REST calls, and `utils.py` hosts filesystem helpers. Prompting and limits are configured in `config.py`. Generated artifacts (source files, TODO/status trackers) land in `files/`, and per-agent transcripts stream to `logs/`. Older evaluation harnesses sit under `examples/<task>/` alongside any zipped datasets.

## Build, Test, and Development Commands
Use the repo's Python uv environment (`uv venv && source .venv/bin/activate`, or `uv run ...`) to guarantee consistent dependency resolution, then install deps with `pip install -U chromadb requests`. Set `config.py` (API key, model, prompt) before launching. Execute the default workflow with `python main.py`; outputs appear in `files/` and `log.txt`. Scenario-specific runners such as `python examples/GSM8k/main.py` reuse the same API surface but load task-specific prompts. Run regression tests with `uv run pytest` from the repo root. If you need to steer sampling, export `MEGAAGENT_TEMPERATURE`; omit it (the default) to lean on OpenAI's built-in temperature of 1 for GPT-5.1 thinking models per the latest docs.

## Coding Style & Naming Conventions
Follow the existing Python style: 4-space indentation, snake_case for modules/functions, CapWords for classes, and prefer f-strings for logging. Keep modules single-responsibility (communication in `llm.py`, orchestration in `agent.py`) and avoid side effects at import time. When adding files under `files/`, make names descriptive (e.g., `files/solver_strategy.py`) so agents can address them deterministically.

## Testing Guidelines
There is no global CI yet, so rely on task-specific runners. Add lightweight self-tests near each entry point and execute them (e.g., dataset harnesses under `examples/`) to validate benchmark logic. Always read the corresponding `logs/<agent>.log` to confirm every agent reached the `terminate` state and that TODO files were cleared before concluding the run. The `uv run pytest` suite enforces 80%+ line coverage on the core runtime, so keep new logic testable.

## Commit & Pull Request Guidelines
Recent history favors short, imperative summaries such as `replacing the set assignment with a dictionary`. Keep subject lines under ~60 chars, group related changes per commit, and reference issues with `#123` when applicable. Pull requests should describe the scenario exercised, list commands run (`python main.py`, dataset tests, etc.), attach any relevant artifacts from `files/`, and mention follow-up risks (e.g., API quota usage). Link logs or evaluation metrics so reviewers can retrace the run.

## Configuration & Security Notes
Never commit real API keys; inject them via environment variables and have `config.py` read from `os.environ` locally. Review any new tools or filesystem write paths carefully—agents can clobber files if prompts are too broad. When sharing logs, scrub sensitive payloads while keeping enough detail for debugging.

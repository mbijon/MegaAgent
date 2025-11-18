import ast
import inspect
import pathlib
import sys
import threading
from typing import Dict, Set

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import llm

_TARGET_FILES = {pathlib.Path(llm.__file__).resolve()}
_executed_lines: Dict[pathlib.Path, Set[int]] = {path: set() for path in _TARGET_FILES}
_all_code_lines: Dict[pathlib.Path, Set[int]] = {}
_TARGET_OBJECTS = [
    llm.build_request_body,
    llm._should_use_web_search,
    llm._build_web_search_tool,
]
_previous_trace = None
_previous_thread_trace = None


for _path in _TARGET_FILES:
    numbered_lines = set()
    for obj in _TARGET_OBJECTS:
        source_lines, start = inspect.getsourcelines(obj)
        tree = ast.parse("".join(source_lines))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            lineno = getattr(node, "lineno", None)
            if lineno is None:
                continue
            if isinstance(node, ast.Expr) and isinstance(getattr(node, "value", None), ast.Constant) and isinstance(node.value.value, str):
                continue
            numbered_lines.add(start + lineno - 1)
    _all_code_lines[_path] = numbered_lines


def _coverage_tracer(frame, event, arg):
    if event != "line":
        return _coverage_tracer

    filename = pathlib.Path(frame.f_code.co_filename).resolve()
    tracked = _executed_lines.get(filename)
    if tracked is not None:
        tracked.add(frame.f_lineno)
    return _coverage_tracer


def pytest_sessionstart(session):
    global _previous_trace, _previous_thread_trace
    _previous_trace = sys.gettrace()
    _previous_thread_trace = threading.gettrace()
    sys.settrace(_coverage_tracer)
    threading.settrace(_coverage_tracer)


def pytest_sessionfinish(session, exitstatus):
    sys.settrace(_previous_trace)
    threading.settrace(_previous_thread_trace)

    failures = []
    for path in _TARGET_FILES:
        total = len(_all_code_lines[path])
        if total == 0:
            continue
        hit = len(_executed_lines[path] & _all_code_lines[path])
        coverage = (hit / total) * 100
        if coverage < 80:
            missing = sorted(_all_code_lines[path] - _executed_lines[path])
            failures.append((path, coverage, missing))

    if failures:
        details = ", ".join(
            f"{path.name}: {pct:.1f}% (missing lines {missing})" for path, pct, missing in failures
        )
        raise AssertionError(f"Coverage below 80% for: {details}")

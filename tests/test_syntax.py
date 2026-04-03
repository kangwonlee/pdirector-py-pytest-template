# begin tests/test_syntax.py
#
# For director (prompt-only) assignments, test_syntax checks:
#   1. prompt.md exists and is not empty
#   2. prompt.md does not contain Python code constructs
#   3. exercise.py was generated and is syntactically valid Python
#   4. exercise.py does not attempt to access grader test files

import ast
import functools
import pathlib
import re
from typing import List

import pytest


# Python code detection patterns
_CODE_PATTERNS = re.compile(
    r'^\s*(def \w|class \w|import \w|from \w.+ import|if .+:|for .+:|while .+:|print\(|[a-zA-Z_]\w*\s*=\s*)',
    re.MULTILINE,
)

# HTML comment pattern for stripping markdown comments
_HTML_COMMENT = re.compile(r'<!--.*?-->', re.DOTALL)

# Suspicious path fragments that indicate test file access attempts
_SUSPICIOUS_PATHS = (
    '/tests/', 'test_results', 'test_syntax', 'test_style',
    'conftest', '/app/ai_tutor', '/app/prompt_pipeline',
)


# ── Prompt checks ──────────────────────────────────────────────


def test__prompt_exists(prompt_path: pathlib.Path):
    assert prompt_path.exists(), (
        f"prompt.md not found at {prompt_path}\n"
        f"{prompt_path} 에서 prompt.md 를 찾을 수 없습니다."
    )


def test__prompt_not_empty(prompt_path: pathlib.Path):
    content = prompt_path.read_text(encoding='utf-8').strip()
    # Strip HTML comments (<!-- ... -->) and # comment lines
    content = _HTML_COMMENT.sub('', content)
    lines = [l for l in content.splitlines()
             if l.strip() and not l.strip().startswith('#')]
    text = '\n'.join(lines).strip()
    assert text, (
        "prompt.md is empty (only comments and headings). "
        "Write a natural language description.\n"
        "prompt.md 가 비어 있습니다 (주석과 제목만 있음). "
        "자연어 설명을 작성하세요."
    )


def test__prompt_no_python_code(prompt_path: pathlib.Path):
    content = prompt_path.read_text(encoding='utf-8')
    matches = _CODE_PATTERNS.findall(content)
    assert not matches, (
        "prompt.md appears to contain Python code. "
        "Write a natural language description, not code.\n"
        "prompt.md 에 Python 코드가 포함된 것으로 보입니다. "
        "코드가 아닌 자연어 설명을 작성하세요.\n"
        f"Detected patterns 감지된 패턴: {[m.strip() for m in matches[:5]]}"
    )


# ── Exercise.py checks ─────────────────────────────────────────


def test__exercise_generated(script_path: pathlib.Path):
    assert script_path.exists(), (
        "exercise.py was not generated. Check the prompt pipeline output.\n"
        "exercise.py 가 생성되지 않았습니다. 프롬프트 파이프라인 출력을 확인하세요."
    )


@functools.lru_cache()
def read_code(script_path: pathlib.Path) -> str:
    return script_path.read_text(encoding="utf-8")


@functools.lru_cache()
def parse_code(script_path: pathlib.Path, proj_folder: pathlib.Path) -> ast.AST:
    try:
        tree = ast.parse(read_code(script_path))
    except SyntaxError as e:
        pytest.fail(
            f"Syntax error in generated code: {script_path.relative_to(proj_folder)}\n"
            f"생성된 코드에 문법 오류: {e}"
        )
    return tree


def test__exercise_syntax_valid(script_path: pathlib.Path, proj_folder: pathlib.Path):
    parse_code(script_path, proj_folder)


# ── Security: prevent test file access ──────────────────────────


def _collect_suspicious_strings(tree: ast.AST) -> List[str]:
    """Walk AST and collect string literals that reference grader paths."""
    suspicious = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            value = node.value
            for pattern in _SUSPICIOUS_PATHS:
                if pattern in value:
                    suspicious.append(value)
                    break
    return suspicious


def _collect_suspicious_imports(tree: ast.AST) -> List[str]:
    """Detect imports commonly used for obfuscation or filesystem probing."""
    suspicious = []
    # Modules that enable code obfuscation or filesystem access
    flagged_modules = {'base64', 'codecs', 'marshal', 'pickle', 'subprocess'}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in flagged_modules:
                    suspicious.append(f"import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.split('.')[0] in flagged_modules:
                suspicious.append(f"from {node.module} import ...")
    return suspicious


def _collect_suspicious_calls(tree: ast.AST) -> List[str]:
    """Walk AST and detect file access calls with suspicious path arguments."""
    suspicious = []
    # Function names that access the filesystem
    fs_funcs = {'open', 'listdir', 'scandir', 'glob', 'iglob', 'walk'}
    # Functions commonly used for obfuscation
    obfuscation_funcs = {'exec', 'eval', 'compile', '__import__'}

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        # Get the function name (handles both 'open' and 'os.listdir')
        func_name = ''
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr

        # Flag obfuscation functions unconditionally
        if func_name in obfuscation_funcs:
            suspicious.append(f"{func_name}(...)")
            continue

        if func_name not in fs_funcs:
            continue

        # Check positional arguments for suspicious paths
        for arg in node.args:
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                for pattern in _SUSPICIOUS_PATHS:
                    if pattern in arg.value:
                        suspicious.append(
                            f"{func_name}({arg.value!r})"
                        )
                        break

    return suspicious


def test__no_test_file_access(script_path: pathlib.Path, proj_folder: pathlib.Path):
    """Reject code that attempts to read grader test files."""
    tree = parse_code(script_path, proj_folder)

    findings = (
        _collect_suspicious_strings(tree)
        + _collect_suspicious_calls(tree)
        + _collect_suspicious_imports(tree)
    )

    assert not findings, (
        "Code attempts to access grader files — this is not allowed.\n"
        "코드가 채점 파일에 접근하려 합니다 — 허용되지 않습니다.\n"
        f"Detected 감지됨: {findings[:5]}"
    )


if __name__ == "__main__":
    pytest.main(['--verbose', __file__])

# end tests/test_syntax.py

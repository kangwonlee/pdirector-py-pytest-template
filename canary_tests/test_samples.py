import pathlib
import shutil
import subprocess
import sys

import pytest


canary_tests_folder = pathlib.Path(__file__).parent.resolve()
proj_folder = canary_tests_folder.parent.resolve()
tests_folder = proj_folder / 'tests'


def discover_samples():
    """Auto-discover sample scripts under sample*/ folders.

    Scripts whose stem ends with '-pass' are expected to pass.
    Scripts whose stem ends with '-fail' are expected to fail.
    """
    for sample_dir in sorted(canary_tests_folder.glob('sample*')):
        if not sample_dir.is_dir():
            continue
        for script in sorted(sample_dir.glob('exercise*.py')):
            if script.name.startswith('test_') or script.name == '__init__.py':
                continue
            stem = script.stem
            if stem.endswith('-pass'):
                expect_pass = True
            elif stem.endswith('-fail'):
                expect_pass = False
            else:
                continue
            yield pytest.param(script, expect_pass, id=f"{sample_dir.name}/{script.name}")


def run_grader(script_path, tmp_path):
    """Copy sample to tmp_path as exercise.py, add dummy prompt.md, run grader tests.

    For prompt-only assignments, the tests expect:
      - exercise.py at STUDENT_CODE_FOLDER
      - prompt.md at /app/workspace (but on host we set it in the same dir)
    """
    sample_dir = script_path.parent

    # Copy exercise sample as exercise.py
    shutil.copy2(script_path, tmp_path / 'exercise.py')

    # Copy sibling files (excluding prompt.md and test files)
    for f in sample_dir.iterdir():
        if f == script_path:
            continue
        if f.name == 'prompt.md':
            continue
        if f.is_file():
            shutil.copy2(f, tmp_path / f.name)

    # Create prompt.md in tmp_path (for prompt_exists / prompt_not_empty tests)
    prompt_src = sample_dir / 'prompt.md'
    if prompt_src.exists():
        shutil.copy2(prompt_src, tmp_path / 'prompt.md')
    else:
        (tmp_path / 'prompt.md').write_text(
            "# Prompt\n\n## Task Description\n\nCanary test dummy prompt.\n"
        )

    return subprocess.run(
        [sys.executable, '-m', 'pytest', str(tests_folder), '-v',
         '-k', 'not git_log and not window_capture'],
        env={
            'PATH': subprocess.os.environ.get('PATH', ''),
            'STUDENT_CODE_FOLDER': str(tmp_path),
            'WORKSPACE_PATH': str(tmp_path),
        },
        capture_output=True,
        text=True,
        timeout=30,
    )


@pytest.mark.parametrize('script_path,expect_pass', discover_samples())
def test_sample(script_path, expect_pass, tmp_path):
    """Run grader tests against a sample submission."""
    result = run_grader(script_path, tmp_path)

    if expect_pass:
        assert result.returncode == 0, (
            f"{script_path.name} should pass all tests.\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
    else:
        assert result.returncode != 0, (
            f"{script_path.name} should fail at least one test.\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )

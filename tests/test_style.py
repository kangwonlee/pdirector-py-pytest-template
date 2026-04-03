# begin tests/test_style.py
import pathlib
import subprocess
from typing import Tuple

import pytest


def test_function_only_in_py_file(script_path: pathlib.Path):
    with open(script_path, 'r') as file:
        lines = file.readlines()

    for line in lines:
        line_strip = line.strip()
        if line.startswith('#') or line.startswith('"""') or line.startswith("'''"):
            continue
        elif line.startswith('def ') and line_strip.endswith(':'):
            continue
        elif line.startswith('import ') or (line.startswith('from ') and ' import ' in line):
            continue
        assert line.startswith(' ') or line_strip == ''


@pytest.fixture
def git_log(proj_folder: pathlib.Path) -> Tuple[str]:
    return tuple(
        subprocess.check_output(
            ['git', 'log', '--pretty=format"%h%x09%an%x09%ad%x09%s"'],
            encoding='utf-8',
            cwd=proj_folder,
        ).splitlines()
    )


def test_git_log(git_log: Tuple[str]):
    new_commits = []
    for line in git_log:
        h, n, d, s = line.split('\t')
        if "github-classroom[bot]" != n:
            new_commits.append(line)
    assert new_commits, "No new commits"


if __name__ == "__main__":
    pytest.main(['--verbose', __file__])

# end tests/test_style.py

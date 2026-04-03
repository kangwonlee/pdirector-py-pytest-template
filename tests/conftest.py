# begin tests/conftest.py

import os
import pathlib

import pytest


# STUDENT_CODE_FOLDER points to CONTAINER_OUTPUT (where exercise.py is generated)
# WORKSPACE_PATH points to the original workspace (with prompt.md)
#   - In Docker: /app/workspace (c_mnt)
#   - On host (canary tests): set to tmp_path by test_samples.py
WORKSPACE_MOUNT = pathlib.Path(os.getenv('WORKSPACE_PATH', '/app/workspace'))


@pytest.fixture
def file_path() -> pathlib.Path:
    p = pathlib.Path(__file__)
    assert p.exists()
    assert p.is_file()
    return p


@pytest.fixture
def my_test_folder(file_path:pathlib.Path) -> pathlib.Path:
    p = file_path.parent.resolve()
    assert p.exists()
    assert p.is_dir()
    return p


@pytest.fixture
def proj_folder(my_test_folder:pathlib.Path) -> pathlib.Path:
    p = pathlib.Path(
        os.getenv(
            'STUDENT_CODE_FOLDER',
            my_test_folder.parent.resolve()
        )
    )
    assert p.exists()
    assert p.is_dir()
    return p


@pytest.fixture
def script_path(proj_folder:pathlib.Path) -> pathlib.Path:
    '''
    Automatically discover ex??.py file
    Force only one ex??.py file in the project folder at the moment
    '''
    exercise_files = tuple(proj_folder.glob('ex*.py'))

    result = None
    if len(exercise_files) == 0:
        raise FileNotFoundError("No Python file starting with 'ex' found in the project folder.")
    elif len(exercise_files) > 1:
        raise ValueError("Multiple Python files starting with 'ex' found in the project folder. Please ensure there is only one.")
    else:
        result = exercise_files[0]

    return result


@pytest.fixture
def workspace_folder() -> pathlib.Path:
    '''Path to the student workspace (git repo with prompt.md)'''
    return WORKSPACE_MOUNT


@pytest.fixture
def prompt_path() -> pathlib.Path:
    '''Path to the student prompt file in the workspace mount'''
    return WORKSPACE_MOUNT / 'prompt.md'

# end tests/conftest.py

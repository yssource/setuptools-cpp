import os
import shutil
import sys
from pathlib import Path
from typing import Iterator, List

import pytest
from _pytest.monkeypatch import MonkeyPatch
from setuptools import setup

from setuptools_cpp import CMakeExtension, ExtensionBuilder, Pybind11Extension, __version__

TESTS_DIR = Path(__file__).parent
PACKAGE_NAME = "test_pkg"


@pytest.fixture
def install_environment(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", [__file__, "install"])


@pytest.fixture(scope="session", autouse=True)
def install_paths() -> Iterator[None]:
    os.chdir(TESTS_DIR)

    # Create package directory
    test_pkg_dir = TESTS_DIR / PACKAGE_NAME
    test_pkg_dir.mkdir(exist_ok=True)

    yield
    for egg_path in TESTS_DIR.iterdir():
        if egg_path.name.endswith("egg-info"):
            shutil.rmtree(str(egg_path))

    # Clean up build files
    for folder in ["build", "dist", "var", PACKAGE_NAME]:
        folder_path = TESTS_DIR / folder
        if folder_path.exists():
            shutil.rmtree(str(folder_path))


def get_pybind_modules(package_name: str) -> List[Pybind11Extension]:
    return [
        Pybind11Extension(f"{package_name}.pybind11.compiled", ["cpp/src/test_pkg.cpp"], include_dirs=["cpp/include"],)
    ]


def get_cmake_modules(package_name: str) -> List[CMakeExtension]:
    return [CMakeExtension(f"{package_name}.cmake.compiled", sourcedir="cpp")]


def test_install(install_environment: None) -> None:
    setup(
        name=PACKAGE_NAME,
        version=__version__,
        ext_modules=[*get_pybind_modules(PACKAGE_NAME), *get_cmake_modules(PACKAGE_NAME)],
        packages=[PACKAGE_NAME],
        cmdclass=dict(build_ext=ExtensionBuilder),
        zip_safe=False,
    )

    from test_pkg.pybind11.compiled import add as pybind_add
    from test_pkg.cmake.compiled import add as cmake_add

    assert pybind_add(1, 1) == 2
    assert cmake_add(1, 1) == 2
# MIT License
#
# Copyright (c) 2026 Pedro Guzmán
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Version helper for pyproject.toml and package init."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

VERSION_RE = re.compile(r'^version\s*=\s*"([^"]+)"', re.M)
INIT_RE = re.compile(r'^__version__\s*=\s*"([^"]+)"', re.M)


def read_version() -> str:
    text = Path("pyproject.toml").read_text(encoding="utf-8")
    match VERSION_RE.search(text):
        case None:
            raise SystemExit("Missing version in pyproject.toml")
        case result:
            return result.group(1)


def write_version(new_version: str) -> None:
    pyproject = Path("pyproject.toml")
    py_text = pyproject.read_text(encoding="utf-8")
    py_text, py_count = VERSION_RE.subn(f'version = "{new_version}"', py_text, count=1)
    match py_count:
        case 1:
            pyproject.write_text(py_text, encoding="utf-8")
        case _:
            raise SystemExit("Version update failed in pyproject.toml")

    init_file = Path("src/docport/__init__.py")
    init_text = init_file.read_text(encoding="utf-8")
    init_text, init_count = INIT_RE.subn(f'__version__ = "{new_version}"', init_text, count=1)
    match init_count:
        case 1:
            init_file.write_text(init_text, encoding="utf-8")
        case _:
            raise SystemExit("Version update failed in __init__.py")


def bump_version(kind: str) -> tuple[str, str]:
    current = read_version()
    parts = current.split(".")
    match len(parts):
        case 3:
            pass
        case _:
            raise SystemExit("Version must be major.minor.patch")

    try:
        major, minor, patch = (int(part) for part in parts)
    except ValueError as err:
        raise SystemExit("Version must be major.minor.patch") from err

    match kind:
        case "major":
            major += 1
            minor = 0
            patch = 0
        case "minor":
            minor += 1
            patch = 0
        case "patch":
            patch += 1
        case _:
            raise SystemExit("Bump must be major, minor, or patch")

    new_version = f"{major}.{minor}.{patch}"
    write_version(new_version)
    return current, new_version


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("get")
    bump = sub.add_parser("bump")
    bump.add_argument("kind", choices=["patch", "minor", "major"])

    args = parser.parse_args()
    match args.command:
        case "get":
            print(read_version())
        case "bump":
            current, new_version = bump_version(args.kind)
            print(f"Bumped version: {current} -> {new_version}")


main()

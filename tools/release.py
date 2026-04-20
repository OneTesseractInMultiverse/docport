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

"""Release helper for interactive version bumps."""

from __future__ import annotations

import shutil
import subprocess

CHOICES = {
    "1": "patch",
    "patch": "patch",
    "2": "minor",
    "minor": "minor",
    "3": "major",
    "major": "major",
}


def pick_kind() -> str:
    print("Select version bump:")
    print("  1) patch")
    print("  2) minor")
    print("  3) major")
    value = input().strip().lower()
    try:
        return CHOICES[value]
    except KeyError as exc:
        raise SystemExit("Invalid choice") from exc


def main() -> None:
    if shutil.which("make") is None:
        raise SystemExit("make is not available on PATH — install make before running a release.")
    kind = pick_kind()
    subprocess.run(["make", f"bump-{kind}"], check=True)


main()

#
# Copyright (c) 2021 Software AG, Darmstadt, Germany and/or its licensors
#
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""Tasks"""
import os
import re
import subprocess
import sys
from invoke import task
from pathlib import Path


@task
def clean(c, docs=False, bytecode=False, extra=""):
    """Clean project (linux only)"""
    patterns = ["build", "dist", "test_output", "deb_dist", "c8ylp*tar.gz"]
    if docs:
        patterns.append("docs/cli")
    if bytecode:
        patterns.append("**/*.pyc")
    if extra:
        patterns.append(extra)
    for pattern in patterns:
        c.run("rm -rf {}".format(pattern))


@task
def lint(c):
    """Lint"""
    c.run("pylint c8ylp")
    c.run("pylint tests/")


@task
def format(c, check=False):
    """Format code (using black)"""
    if check:
        c.run("black --check --target-version=py37 .")
    else:
        c.run(f"{sys.executable} -m black --target-version=py37 .")


@task
def build(c):
    """Build"""
    c.run(f"{sys.executable} setup.py sdist bdist_wheel")


@task(pre=[clean])
def build_deb(c):
    """Build debian package - (Debian/Ubuntu only)

    apt-get install -y python-all dh-python python3-stdeb
    """
    print("Warning: Requires package 'python-all dh-python python3-stdeb' to work")
    c.run(f"{sys.executable} setup.py --command-packages=stdeb.command bdist_deb")

    print("\nThe debian file is stored under: deb_dist/*.deb\n")


@task(pre=[build])
def publish(c):
    """Publish python package to pip"""
    if "TWINE_USERNAME" not in os.environ or "TWINE_PASSWORD" not in os.environ:
        print(
            "'TWINE_USERNAME' and 'TWINE_PASSWORD' environment variables "
            "are required for publishing"
        )
        sys.exit(1)

    c.run("twine upload dist/*")


@task
def test(c, pattern=None):
    """Run unit tests and coverage report"""
    cmd = [
        "pytest",
        "tests",
        "--timeout=10",
        # Note: Don't use log cli level (--log-cli-level) as it can affect click testing!
        "--cov-config=.coveragerc",
        "--cov-report=term",
        "--cov-report=html:test_output/htmlcov",
        "--cov=c8ylp",
    ]

    if pattern:
        cmd.append(f"-k={pattern}")
    c.run(" ".join(cmd))


@task(pre=[clean])
def test_integration(c, pattern=None):
    """Run integration tests"""
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "--durations=0",
        "--timeout=3600",
        "--log-cli-level=INFO",
        "--cov-config=.coveragerc",
        "--cov-report=term",
        "--cov-report=html:test_output/htmlcov",
        "--cov=c8ylp",
    ]

    assert os.path.exists(".env") or os.environ.get(
        "C8Y_HOST"
    ), "Missing Cumulocity configuration required for integration tests"

    if pattern:
        cmd.append(f"-k={pattern}")
    c.run(" ".join(cmd))


@task
def generate_docs(c):
    """Generate cli docs (markdown files)"""
    commands = [
        ("c8ylp",),
        (
            "c8ylp",
            "login",
        ),
        (
            "c8ylp",
            "server",
        ),
        (
            "c8ylp",
            "connect",
        ),
        (
            "c8ylp",
            "connect",
            "ssh",
        ),
        (
            "c8ylp",
            "plugin",
        ),
        (
            "c8ylp",
            "plugin",
            "command",
        ),
        (
            "c8ylp",
            "version",
        ),
    ]

    doc_dir = Path("docs") / "cli"
    doc_dir.mkdir(parents=True, exist_ok=True)

    for cmd in commands:
        name = "_".join(cmd).upper() + ".md"
        doc_file = doc_dir / name
        print(f"Updating cli doc: {str(doc_file)}")

        proc = subprocess.run(
            [sys.executable, "-m", *cmd, "--help"],
            stdout=subprocess.PIPE,
            env={
                **os.environ,
                "C8Y_HOST": "dummy",
                "C8YLP_PLUGINS": "dummy",
            },
        )

        usage = proc.stdout.decode()

        # Replace python3 module usage, to the more common c8ylp
        usage = re.sub("python3? -m ", "", usage)

        # Strip plugin folder information out of usage
        usage = re.sub(r"Checking plugin folder.+\n", "", usage)

        doc_template = f"""
## {" ".join(cmd)}

```
{usage}
```
"""

        doc_file.write_text(doc_template)


@task
def add_license(c):
    """Add license header to source files"""
    c.run(
        f"{sys.executable} -m licenseheaders --current-year --owner 'Software AG, Darmstadt, Germany' -E .py -t licence_header.tmpl -d ."
    )

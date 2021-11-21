"""Tasks"""
import os
import subprocess
from invoke import task
from pathlib import Path


@task
def clean(c, docs=False, bytecode=False, extra=""):
    patterns = ["build"]
    if docs:
        patterns.append("docs/_build")
    if bytecode:
        patterns.append("**/*.pyc")
    if extra:
        patterns.append(extra)
    for pattern in patterns:
        c.run("rm -rf {}".format(pattern))


@task
def build(c):
    """Build"""
    c.run("python setup.py build")


@task
def lint(c):
    """Lint"""
    c.run("python3 -m pylint c8ylp")
    c.run("python3 -m pylint tests/")


@task
def format(c, check=False):
    """Format code (using black)"""
    if check:
        c.run("python3 -m black --check --target-version=py37 .")
    else:
        c.run("python3 -m black --target-version=py37 .")


@task
def test(c, pattern=None):
    """Run unit tests and coverage report"""
    cmd = [
        "python3",
        "-m",
        "pytest",
        "tests",
        "--timeout=10",
        # Note: Dont use log cli level (--log-cli-level) as it can affect click testing!
        "--cov-config=.coveragerc",
        "--cov-report=term",
        "--cov-report=html:test_output/htmlcov",
        "--cov=c8ylp",
    ]

    if pattern:
        cmd.append(f"-k={pattern}")
    c.run(" ".join(cmd))


@task
def test_integration(c, pattern=None):
    """Run integration tests"""
    cmd = [
        "python3",
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
def test_performance(c, testid=2):
    """
    Run performance tests for specific scenarios
    """

    pypaths = [
        os.getcwd(),
        os.getenv("PYTHONPATH"),
    ]
    pypaths = [x for x in pypaths if x]

    c.run("python3 ./tests/performance/create-file.py ./tests/performance/5.mb 5")

    env = {
        **os.environ,
        "C8Y_DEVICE": "device01",
        "PYTHONPATH": ":".join(pypaths),
    }

    if testid == 1:
        c.run("./tests/performance/test1_file_transfer.sh", env=env)
    elif testid == 2:
        c.run("./tests/performance/test2_file_transfer_concurrent.sh", env=env)
    elif testid == 3:
        c.run("./tests/performance/test3_concurrent_single_commands.sh", env=env)


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
    ]

    doc_dir = Path("docs") / "cli"
    doc_dir.mkdir(parents=True, exist_ok=True)

    for cmd in commands:
        name = "_".join(cmd).upper() + ".md"
        doc_file = doc_dir / name
        print(f"Updating cli doc: {str(doc_file)}")
        proc = subprocess.run(["python3", "-m", *cmd, "--help"], stdout=subprocess.PIPE)

        usage = proc.stdout.decode().replace("python -m ", "", -1)
        doc_template = f"""
## {" ".join(cmd)}

```
{usage}
```
"""

        doc_file.write_text(doc_template)

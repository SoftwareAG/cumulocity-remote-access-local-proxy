"""Tasks"""
import os
from invoke import task


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
def format(c):
    """Format code (using black)"""
    c.run("python3 -m black --target-version=py37 .")


@task
def test(c, pattern=None):
    """Run unit tests and coverage report"""
    cmd = [
        "python3",
        "-m",
        "pytest",
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
        "C8Y_DEVICE": "cb4-a2euccg1p22111000141",
        "PYTHONPATH": ":".join(pypaths),
    }

    if testid == 1:
        c.run("./tests/performance/test1_file_transfer.sh", env=env)
    elif testid == 2:
        c.run("./tests/performance/test2_file_transfer_concurrent.sh", env=env)
    elif testid == 3:
        c.run("./tests/performance/test3_concurrent_single_commands.sh", env=env)

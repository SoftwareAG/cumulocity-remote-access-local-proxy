"""Tasks"""
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


@task
def format(c):
    """Format code (using black)"""
    c.run("python3 -m black --target-version=py37 .")

# flake8: noqa

"""
Ultralight "smoke test" that simply verifies the test runner
and import machinery work. It does nothing more than attempt
to import a couple of common modules.
"""

def test_repo_imports():
    import importlib      # noqa: F401
    import pkg_resources  # noqa: F401

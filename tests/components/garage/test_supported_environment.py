"""Keep current test versions separate from the supported HA minimum."""

import json
from importlib.metadata import version
from pathlib import Path

from packaging.requirements import Requirement
from packaging.version import Version


def _pinned_versions(path):
    return {
        requirement.name: next(iter(requirement.specifier)).version
        for line in path.read_text().splitlines()
        if line.strip() and not line.startswith(("#", "-"))
        for requirement in [Requirement(line)]
        if str(requirement.specifier).startswith("==")
    }


def test_supported_environments_match_installed_home_assistant():
    """Verify actual HA/plugin versions without conflating tests and support."""
    root = Path(__file__).resolve().parents[3]
    support_minimum = json.loads((root / "hacs.json").read_text())["homeassistant"]
    current = _pinned_versions(root / "requirements_test.txt")
    minimum = _pinned_versions(root / "requirements_test_min.txt")
    assert minimum["homeassistant"] == support_minimum
    assert Version(current["homeassistant"]) >= Version(support_minimum)
    actual = version("homeassistant")
    expected = next(
        environment
        for environment in (current, minimum)
        if environment["homeassistant"] == actual
    )
    assert (
        version("pytest-homeassistant-custom-component")
        == expected["pytest-homeassistant-custom-component"]
    )

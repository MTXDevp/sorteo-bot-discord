"""Fixtures compartidas."""

import random

import pytest


@pytest.fixture()
def rng() -> random.Random:
    """RNG con semilla fija para sorteos deterministas."""
    return random.Random(42)

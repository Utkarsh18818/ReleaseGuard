from dataclasses import replace
from uuid import uuid4

import pytest
from releaseguard.adapters.falkordb import GraphStore
from releaseguard.application.ingestion import load_dataset, seed
from releaseguard.config import ROOT, Settings


@pytest.fixture
def store(tmp_path):
    settings = replace(Settings.load(), graph="releaseguard_test_" + uuid4().hex)
    instance = GraphStore(settings, lock_directory=tmp_path)
    seed(instance, load_dataset(ROOT / "fixtures" / "northstar.json"))
    yield instance
    assert instance.name.startswith("releaseguard_test_")
    instance.graph.delete()


@pytest.fixture
def dataset():
    return load_dataset(ROOT / "fixtures" / "northstar.json")

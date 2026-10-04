import pytest
from work2030.store import Store
from work2030.services import Services


@pytest.fixture
def store(tmp_path):
    return Store(tmp_path / "test.sqlite")


@pytest.fixture
def session(store):
    return store.create("Test")


@pytest.fixture
def services(store):
    return Services(store)

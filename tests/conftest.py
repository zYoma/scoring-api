import pytest
import threading
from http.server import HTTPServer
from unittest.mock import Mock, patch

from api import MainHTTPHandler
from store import BaseStore, StoreKeyNotFound


class MockStore(BaseStore):

    def cache_set(self, key, data, ttl):
        self.store[key] = data

    def cache_get(self, key):
        return self.store.get(key)

    def get(self, key):
        if value := self.cache_get(key):
            return value
        raise StoreKeyNotFound

    def _setup(self):
        self.store = {'i:1': '{"key": "value"}', 'i:2': '{"key": "value"}', 'i:3': '{"key": "value"}'}


@pytest.fixture(scope='module')
def server():
    """ Мокаю атрибут store класса MainHTTPHandler. Вместо редиса использую в тестах MockStore.
        Для интеграционных тестов запускаю сервер в отдельном потоке демоне.
    """
    with patch('api.MainHTTPHandler.store', new_callable=MockStore):
        server = HTTPServer(("localhost", 8080), MainHTTPHandler)
        thread = threading.Thread(target=server.serve_forever)
        thread.daemon = True
        thread.start()
        yield


@pytest.fixture()
def mock_token():
    """Фикстура мокает check_auth, чтобы всегда проходить авторизацию."""
    with patch("api.check_auth", new_callable=lambda *args: Mock(return_value=True)):
        yield

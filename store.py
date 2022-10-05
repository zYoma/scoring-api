from typing import Type

import os
import redis
import time
from abc import ABC
from logging import getLogger


logger = getLogger()
REDIS_DSN = os.environ.get('REDIS_DSN', 'redis://127.0.0.1:6379/0')
MAX_RETRIES = 3
CONNECT_TIMEOUT = 2


class StoreKeyNotFound(Exception):
    @staticmethod
    def get_message():
        return 'Данные по клиентам не найдены'


class BaseStore(ABC):
    def __init__(self):
        self._setup()

    def cache_set(self, key, data, ttl):
        """Сохранение данных в кеш по ключу."""
        raise NotImplementedError

    def cache_get(self, key):
        """Получение данных из кеша по ключу. Доступность store неважно."""
        raise NotImplementedError

    def get(self, key):
        """Получение данных по ключу. Если store недоступен, вернет ошибку."""
        raise NotImplementedError

    def _setup(self):
        """Подключение к стору."""
        raise NotImplementedError


def trying_factory(error: Type[Exception]):
    """ Декоратор, принимает на вход ошибку соответсвующую конкретному store.
        Если возникает переданная ошибка, делает повторную попытку обращения к store.
        Если число попыток превышает MAX_RETRIES, выбрасывает исключение.
    """
    def trying(func):
        def wrap(*args, **kwargs):
            max_retries = MAX_RETRIES
            count = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except error:
                    count += 1
                    if count > max_retries:
                        raise

                    backoff = count * 2
                    logger.error('Retrying in {} seconds'.format(backoff))
                    time.sleep(backoff)
        return wrap
    return trying


class RedisStore(BaseStore):

    @trying_factory(error=redis.exceptions.RedisError)
    def cache_set(self, key, data, ttl):
        self.store.set(key, data, ex=ttl)

    @trying_factory(error=redis.exceptions.RedisError)
    def cache_get(self, key):
        if value := self.store.get(key):
            return float(value.decode())

    def get(self, key):
        if value := self.cache_get(key):
            return value
        raise StoreKeyNotFound

    def _setup(self):
        self.store = redis.Redis.from_url(REDIS_DSN, socket_connect_timeout=CONNECT_TIMEOUT)

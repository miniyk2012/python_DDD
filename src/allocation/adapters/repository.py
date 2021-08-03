import abc
from allocation.domain import model


class AbstractProductRepository(abc.ABC):
    @abc.abstractmethod
    def add(self, product: model.Product):
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, sku) -> model.Product:
        raise NotImplementedError


class ProductRepository(AbstractProductRepository):
    def __init__(self, session):
        self.session = session

    def add(self, product):
        pass

    def get(self, sku):
        pass

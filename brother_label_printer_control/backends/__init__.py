from __future__ import annotations

from abc import ABC, abstractmethod


class BaseBackend(ABC): ...


class UniDirectionalBackend(BaseBackend):
    @abstractmethod
    def write(self, data: bytes): ...


class BiDirectionalBackend(UniDirectionalBackend):
    @abstractmethod
    def read(self, count: int) -> bytes: ...

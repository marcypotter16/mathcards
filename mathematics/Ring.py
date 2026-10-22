
from mathematics.Math import UnitaryRing
from mathematics.Polynomials import Polynomial


class ZZ(UnitaryRing):
    """The ring of integers"""
    def __init__(self) -> None:
        self.zero = 0
        self.one = 1

    def validate(self) -> None:
        pass

    def add(self, e1, e2):
        return e1 + e2

    def multiply(self, e1, e2):
        return e1 * e2

class ZZn(ZZ):
    class ModuloGreaterThan1(ValueError):
        pass

    """The ring of integers modulo n"""
    def __init__(self, n: int) -> None:
        super().__init__()
        if n < 2:
            raise self.ModuloGreaterThan1("n has to be at least 2")
        self.n = n

    def add(self, e1, e2):
        return (e1 + e2) % self.n

    def multiply(self, e1, e2):
        return (e1 * e2) % self.n

    def reduce_mod(self, e):
        return e % self.n

class PolyRing[T](UnitaryRing[Polynomial[T]]):
    """
    The ring of polynomials R[x] over a given coefficient ring R.
    It is itself a UnitaryRing whose elements are Polynomial[T] instances.
    """
    def __init__(self, coefficient_ring: UnitaryRing[T]) -> None:
        self.coefficient_ring = coefficient_ring
        # Zero polynomial: 0 * x^0
        self.zero = Polynomial({0: coefficient_ring.zero}, coefficient_ring)
        # Unit polynomial: 1 * x^0
        self.one = Polynomial({0: coefficient_ring.one}, coefficient_ring)

    def validate(self) -> None:
        # Infinite structure, skip finite axiom checks
        pass

    def add(self, p1: Polynomial[T], p2: Polynomial[T]) -> Polynomial[T]:
        return p1 + p2

    def multiply(self, p1: Polynomial[T], p2: Polynomial[T]) -> Polynomial[T]:
        return p1 * p2
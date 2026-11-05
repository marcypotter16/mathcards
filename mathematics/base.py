# from typing import *

from enum import StrEnum, auto
from math import ceil
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, TypeVar
from pyray import Rectangle, Vector2

T = TypeVar("T")

type BinaryOp[T] = Callable[[T, T], T] | Dict[Tuple[T, T], T]
type MorphismMap[SourceT, TargetT] = Callable[[SourceT], TargetT] | Dict[SourceT, TargetT]

def _op(operation: BinaryOp[T], a: T, b: T) -> T:
    if isinstance(operation, dict):
        return operation[(a, b)]
    return operation(a, b)

class Category(StrEnum):
    AbGp    = "Abelian_Groups"
    CRings  = "Commutative_Rings"

class AlgebraicStructure[T]:
    def validate(self):
        return NotImplemented

    def is_finite(self) -> bool:
        return NotImplemented

    @property
    def typst_str(self) -> str:
        return NotImplemented

    def get_random_element(self) -> T:
        return NotImplemented

    def __contains__(self, item):
        return NotImplemented

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, AlgebraicStructure):
            return False
        return self.typst_str == value.typst_str

    def __hash__(self) -> int:
        return NotImplemented

    @staticmethod
    def find_identity(elements: Set[T], operation: BinaryOp[T]) -> Optional[T]:
        """Finds the identity element 'e' if it exists."""
            
        for candidate in elements:
            is_identity = True
            for a in elements:
                if _op(operation, a, candidate) != a or _op(operation, candidate, a) != a:
                    is_identity = False
                    break
            if is_identity:
                print(f"Neutral element is {candidate}")
                return candidate
        return None

    @staticmethod
    def find_one(elements: Set[T], product: BinaryOp[T], zero: T) -> T:
        """Finds the multiplicative identity '1' if it exists (ignoring zero)."""
        for candidate in elements:
            if candidate == zero:
                continue
                
            is_one = True
            for a in elements:
                # 1 * a == a and a * 1 == a
                if _op(product, candidate, a) != a or _op(product, a, candidate) != a:
                    is_one = False
                    break
                    
            if is_one:
                print(f"Multiplicative identity (1) is {candidate}")
                return candidate
                
        raise NeutralElementNotFound("Validation Failed: No multiplicative identity found.")

    @staticmethod
    def check_associativity(elements: Set[T], operation: BinaryOp[T]) -> bool:
        # 2. Check Associativity: (a + b) + c == a + (b + c)
        for a in elements:
            for b in elements:
                for c in elements:
                    left = _op(operation, _op(operation, a, b), c)
                    right = _op(operation, a, _op(operation, b, c))
                    if left != right:
                        return False
        return True

    @staticmethod
    def check_commutativity(elements: Set[T], operation: BinaryOp[T]) -> bool:
        for e in elements:
            for f in elements:
                ef = _op(operation, e, f)
                fe = _op(operation, f, e)
                if ef != fe:
                    return False
        return True

class NotAbelian(ValueError):
    pass

class NeutralElementNotFound(ValueError):
    pass

class NotAllElementsInvertible(ValueError):
    pass

class OperationNotAssociative(ValueError):
    pass

class RingProductNotDistributive(ValueError):
    pass

class AdditiveGroup[T](AlgebraicStructure[T]):
    def __init__(self, elements: Set[T], gp_operation: BinaryOp[T]) -> None:
        self.elements:      Set[T]              = elements
        self.gp_operation                       = gp_operation
        self.zero:          T | None            = None
        self.generators:    Set[T] | None       = None
        self.validate()

    def add(self, e1: T, e2: T) -> T:
        if isinstance(self.gp_operation, dict):
            pair = (e1, e2)
            if pair not in self.gp_operation:
                raise KeyError(f"Pair {pair} is not defined in this group's operation table.")
            # print(f"+{pair} = {self.operation[pair]}")
            return self.gp_operation[pair]
        return self.gp_operation(e1, e2)

    def neg(self, e1: T) -> T:
        for el in self.elements:
            if self.add(e1, el) == self.zero:
                return el
        raise NotAllElementsInvertible(f"Element {e1} is not invertible (this shouldn't happen!)")

    def sub(self, e1: T, e2: T):
        return self.add(e1, self.neg(e2))

    def validate(self) -> None:
        """Validates identity, invertibility, and associativity for finite groups."""
        self.zero = AlgebraicStructure.find_identity(self.elements, self.gp_operation)

        if self.zero is None:
            raise NeutralElementNotFound("Validation Failed: No identity element found.")

        # 1. Check Invertibility
        for a in self.elements:
            has_inverse = False
            for b in self.elements:
                if self.add(a, b) == self.zero and self.add(b, a) == self.zero:
                    has_inverse = True
                    break
            if not has_inverse:
                raise NotAllElementsInvertible(f"Validation Failed: Element {a} has no inverse.")

        res = AlgebraicStructure.check_associativity(self.elements, self.gp_operation)
        if not res:
            raise OperationNotAssociative(f"Validation Failed: Associativity fails.")

        print(f"Group successfully validated! Identity is {self.zero}.")


class AbelianGroup[T](AdditiveGroup[T]):
    def __init__(self, elements: Set[T], gp_operation: BinaryOp[T]) -> None:
        super().__init__(elements, gp_operation)

    def validate(self) -> None:
        super().validate()
        ab = AlgebraicStructure.check_commutativity(self.elements, self.gp_operation)
        if not ab:
            raise NotAbelian(f"Group {self.elements} is not abelian")


class CommUnitRing[T](AbelianGroup[T]):
    def __init__(self, elements: Set[T], gp_operation: BinaryOp[T], product: BinaryOp[T]) -> None:
        self.elements:      Set[T]          = elements
        self.gp_operation:  BinaryOp[T]     = gp_operation
        self.product:       BinaryOp[T]     = product
        self.validate()
        self.zero:          T               = self.zero # type: ignore because it has to exist
        self.one:           T               = AlgebraicStructure.find_one(self.elements, self.product, self.zero)


    def multiply(self, e1: T, e2: T) -> T:
        if isinstance(self.product, dict):
            pair = (e1, e2)
            if pair not in self.product:
                raise KeyError(f"Pair {pair} is not defined in this ring's multiplication table.")
            # print(f"+{pair} = {self.operation[pair]}")
            return self.product[pair]
        return self.product(e1, e2)

    def pow(self, e1: T, exp: int) -> T:
        if exp == 0:
            return self.one # Assuming your ring has a multiplicative identity 'one'
        
        res = e1
        for _ in range(exp - 1):
            res = self.multiply(res, e1)  # Multiply by the original base, NOT res by res!
        return res

    def mult_inv(self, e1: T) -> T | None:
        for el in self.elements:
            if self.multiply(e1, el) == self.one:
                return el
        return None

    def is_invertible(self, e1: T) -> bool:
        return self.mult_inv(e1) is not None

    def is_field(self) -> bool:
        return all(self.is_invertible(el) for el in self.elements if el != self.zero)

    def is_domain(self) -> bool:
        return NotImplemented

    def validate(self) -> None:
        super().validate()
        AlgebraicStructure.check_associativity(self.elements, self.product)

        # Distributive law
        for e in self.elements:
            for f in self.elements:
                for g in self.elements:
                    # e (f + g) = ef + eg
                    left = self.multiply(e, self.add(f, g))
                    right = self.add(self.multiply(e, f), self.multiply(e, g))
                    if left != right:
                        raise RingProductNotDistributive(f"{e}({f}+{g}) = {left} != {e}*{f} + {e}*{g} = {right}")
                    # (e + f) g = eg + fg
                    left = self.multiply(self.add(e, f), g)
                    right = self.add(self.multiply(e, g), self.multiply(f, g))
                    if left != right:
                        raise RingProductNotDistributive(f"({e}+{f}){g} = {left} != {e}*{g} + {f}*{g} = {right}")

        print("Ring is distributive and OK")

    def divides(self, e1: T, e2: T) -> T | None:
        """If e1 divides e2 it returns x such that e1 * x = e2, otherwise returns None"""
        for e in self.elements:
            prod = self.multiply(e1, e)
            if prod == e2:
                return prod
        return None


class Ideal[T](AbelianGroup[T]):
    """Base class for ideals, probably should not be instantiated"""
    generators: Set[T]

    def __init__(self, generators: Set[T], ring: CommUnitRing[T]) -> None:
        self.generators = generators
        self.ring = ring

    def is_prime(self) -> bool:
        return NotImplemented

    def is_maximal(self) -> bool:
        return NotImplemented
    
    @property
    def typst_str(self) -> str:
        return f"({', '.join(gen.typst_str for gen in self.generators)})" # type: ignore

    def get_random_element_in_complementary(self) -> T:
        """Useful for localization at prime ideals, where invertible elements are from the complementary of the ideal."""
        return NotImplemented
    
    def __repr__(self) -> str:
        return f"({self.generators})"

class PrincipalIdeal[T](Ideal[T]):
    generator: T
    def __init__(self, generator: T, ring: CommUnitRing[T]) -> None:
        self.ring = ring
        self.generators = { generator }
        self.generator = generator

    @property   
    def typst_str(self) -> str:
        if hasattr(self.generator, "typst_str"):
            return f"({self.generator.typst_str})" # type: ignore
        raise ValueError("Generator for some reason doesn't have typst str method")

    def __repr__(self) -> str:
        return f"({self.generator})"

class QuotGroup(AdditiveGroup):
    pass

# Generic over the *element types* (e.g., int, int)
class Morphism[SourceElementT, TargetElementT]:
    def __init__(
        self, 
        source: AdditiveGroup[SourceElementT], 
        target: AdditiveGroup[TargetElementT], 
        mapping: MorphismMap[SourceElementT, TargetElementT]
    ) -> None:
        self.source = source
        self.target = target
        self._mapping = mapping

    def __call__(self, element: SourceElementT) -> TargetElementT:
        if isinstance(self._mapping, dict):
            if element not in self._mapping:
                raise KeyError(f"Element {element} has no mapping defined.")
            return self._mapping[element]
        return self._mapping(element)

    @property
    def kernel(self) -> Set[SourceElementT]:
        if not self.source.is_finite():
            return NotImplemented("Kernel for infinite groups is not yet implemented")
        return { el for el in self.source.elements if self(el) == self.target.zero }

    @property
    def image(self) -> Set[TargetElementT]:
        return { self(el) for el in self.source.elements }

def is_prime(n: int) -> bool:
    """The most basic primality test, for small numbers it's enough"""
    for i in range(2, ceil(n*.5) + 1):
        if n % i == 0:
            return False
    return True

def factorize(n: int) -> dict[int, int]:
    """Returns a dictionary mapping prime factors to their exponents: {p: exp}."""
    n = abs(n)
    factors = {}
    
    # Handle small edge cases
    if n <= 1:
        return factors
        
    d = 2
    while d * d <= n:
        if n % d == 0:
            count = 0
            while n % d == 0:
                count += 1
                n //= d
            factors[d] = count
        d += 1
        
    if n > 1:
        factors[n] = 1
        
    return factors

def get_rect_center(r: Rectangle) -> Vector2:
    return Vector2(r.x + r.width / 2, r.y + r.height / 2)

if __name__ == "__main__":
    elements = {0, 1}
    operation = {
        (0, 0): 0,
        (0, 1): 1,
        (1, 0): 1,
        (1, 1): 0
    }
    prod = {
        (0, 0): 0,
        (0, 1): 0,
        (1, 0): 0,
        (1, 1): 1
    }
    g1 = CommUnitRing[int](elements, operation, prod)
    g2 = CommUnitRing[int](elements, operation, prod)
    mapping = {
        0: 0,
        1: 0
    }
    mo = Morphism(g1, g2, mapping)
    print(mo.kernel, mo.image) # {0, 1} {0}

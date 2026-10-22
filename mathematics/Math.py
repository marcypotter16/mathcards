# from typing import *

from typing import Any, Callable, Dict, List, Optional, Set, Tuple, TypeVar

T = TypeVar("T")

BinaryOp = Callable[[T, T], T] | Dict[Tuple[T, T], T]

def _op(operation: BinaryOp, a: T, b: T) -> T:
    if isinstance(operation, dict):
        return operation[(a, b)]
    return operation(a, b)

class AlgebraicStructure[T]:

    def validate(self):
        pass

    @staticmethod
    def find_identity(elements: Set[T], operation: BinaryOp) -> Optional[T]:
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
    def find_one(elements: Set[T], product: BinaryOp, zero: T) -> T:
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
    def check_associativity(elements: Set[T], operation: BinaryOp) -> bool:
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
    def check_commutativity(elements: Set[T], operation: BinaryOp) -> bool:
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
    def __init__(self, elements: Set[T], gp_operation: BinaryOp) -> None:
        self.elements:      Set[T]              = elements
        self.gp_operation                       = gp_operation
        self.identity:      T | None            = None
        self.validate()

    def add(self, e1: T, e2: T) -> T:
        if isinstance(self.gp_operation, dict):
            pair = (e1, e2)
            if pair not in self.gp_operation:
                raise KeyError(f"Pair {pair} is not defined in this group's operation table.")
            # print(f"+{pair} = {self.operation[pair]}")
            return self.gp_operation[pair]
        return self.gp_operation(e1, e2)

    def validate(self) -> None:
        """Validates identity, invertibility, and associativity for finite groups."""
        self.identity = AlgebraicStructure.find_identity(self.elements, self.gp_operation)

        if self.identity is None:
            raise NeutralElementNotFound("Validation Failed: No identity element found.")

        # 1. Check Invertibility
        for a in self.elements:
            has_inverse = False
            for b in self.elements:
                if self.add(a, b) == self.identity and self.add(b, a) == self.identity:
                    has_inverse = True
                    break
            if not has_inverse:
                raise NotAllElementsInvertible(f"Validation Failed: Element {a} has no inverse.")

        res = AlgebraicStructure.check_associativity(self.elements, self.gp_operation)
        if not res:
            raise OperationNotAssociative(f"Validation Failed: Associativity fails.")

        print(f"Group successfully validated! Identity is {self.identity}.")


class AbelianGroup[T](AdditiveGroup[T]):
    def __init__(self, elements: Set[T], gp_operation: BinaryOp) -> None:
        super().__init__(elements, gp_operation)

    def validate(self) -> None:
        super().validate()
        ab = AlgebraicStructure.check_commutativity(self.elements, self.gp_operation)
        if not ab:
            raise NotAbelian(f"Group {self.elements} is not abelian")


class UnitaryRing[T](AbelianGroup[T]):
    def __init__(self, elements: Set[T], gp_operation: BinaryOp, product: BinaryOp) -> None:
        self.elements:      Set[T]          = elements
        self.gp_operation:  BinaryOp        = gp_operation
        self.product:       BinaryOp        = product
        self.validate()
        self.zero:          T               = self.identity # type: ignore because it has to exist
        self.one:           T               = AlgebraicStructure.find_one(self.elements, self.product, self.zero)


    def multiply(self, e1, e2):
        if isinstance(self.product, dict):
            pair = (e1, e2)
            if pair not in self.product:
                raise KeyError(f"Pair {pair} is not defined in this ring's multiplication table.")
            # print(f"+{pair} = {self.operation[pair]}")
            return self.product[pair]
        return self.product(e1, e2)

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
    g = UnitaryRing[int](elements, operation, prod)
    print(g.zero, g.one)

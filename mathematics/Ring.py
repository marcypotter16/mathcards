
from typing import Any, Set, SupportsIndex
from sympy import Poly
from sympy.abc import x

from math import gcd, lcm
from mathematics.Math import Ideal, PrincipalIdeal, UnitaryRing, factorize, is_prime
from mathematics.Polynomials import MonicPolynomial, Monomial, Polynomial


class ZZ(UnitaryRing):
    """The ring of integers"""
    def __init__(self) -> None:
        self.zero = 0
        self.one = 1
        self.generators = {1}

    def is_finite(self):
        return False

    def validate(self) -> None:
        pass

    def add(self, e1, e2):
        return e1 + e2

    def multiply(self, e1, e2):
        return e1 * e2

    def is_field(self) -> bool:
        return False

    def typst_str(self) -> str:
        return "ZZ"

    def gcd(self, *integers: SupportsIndex):
        return gcd(*integers)

    def lcm(self, *integers: SupportsIndex):
        return lcm(*integers)

    def divides(self, a: int, b: int) -> int | None:
        val = b // a
        if val != 0:
            return None
        return val

    def __repr__(self) -> str:
        return "ZZ"

class ZZn(UnitaryRing):
    """The ring of integers modulo n"""
    class ModuloGreaterThan1(ValueError):
        pass
    def __init__(self, n: int) -> None:
        if n < 2:
            raise self.ModuloGreaterThan1("The modulus has to be at least 2")
        self.n = n
        self.zero = 0
        self.one = 1
        self.elements = set(range(n))

    def is_finite(self):
        return True

    def is_field(self) -> bool:
        return is_prime(self.n)

    def add(self, e1, e2):
        return (e1 + e2) % self.n

    def multiply(self, e1, e2):
        return (e1 * e2) % self.n

    def mult_inv(self, e1: int) -> int | None:
        try:
            return pow(e1, -1, self.n)
        except ValueError:
            return None

    def divides(self, a: int, b: int) -> int | None:
        """
        Solves a * x ≡ b (mod n). Returns a valid x if a solution exists, else None.
        """
        a = a % self.n
        b = b % self.n
        
        if a == 0:
            return 0 if b == 0 else None
            
        g = gcd(a, self.n)
        
        # A solution exists if and only if g divides b
        if b % g != 0:
            return None
            
        # Reduce the equation by g
        a_prime = a // g
        b_prime = b // g
        n_prime = self.n // g
        
        # Now a_prime and n_prime are coprime, so a_prime is invertible mod n_prime
        inv = pow(a_prime, -1, n_prime)
        x = (b_prime * inv) % n_prime
        
        return x

    def reduce_mod(self, e):
        return e % self.n

    def typst_str(self) -> str:
        return f"ZZ_({self.n})"

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return f"ZZ/({self.n})"

class IntegerIdeal(Ideal[int]):
    def __init__(self, generators: Set[int], ring: UnitaryRing[int]) -> None:
        super().__init__(generators, ring)
        self.generator = gcd(*self.generators) if self.generators else 0

    def is_prime(self) -> bool:
        return is_prime(self.generator)

    def is_maximal(self) -> bool:
        return self.is_prime()

    def is_radical(self) -> bool:
        if self.generator == 0:
            return True
        factors = factorize(self.generator)
        return all(power == 1 for power in factors.values())

    def __contains__(self, item):
        return item % self.generator == 0

class PrincipalPolyIdeal(PrincipalIdeal[Polynomial]):
    def __init__(self, generator: Polynomial, ring: PolyRing) -> None:
        self.generator = generator
        self.coeff_r = ring.coefficient_ring
        self.ring = ring

    def __contains__(self, item):
        return item // self.generator == Polynomial.zero(self.ring)

    def is_prime(self) -> bool:
        print(f"Testing {self.generator}, {self.ring.typst_str()}")
        if self.generator.is_zero:
            return True
        if isinstance(self.coeff_r, ZZ) or isinstance(self.coeff_r, QQ):
            p = self.generator.to_sympy(modulus=None)
            return p.is_irreducible
        if isinstance(self.coeff_r, ZZn):
            p = self.generator.to_sympy(modulus=self.coeff_r.n)
            return p.is_irreducible
        raise NotImplemented

class Frac[T]: 
    def __init__(self, num: T, denom: T, ring: UnitaryRing[T] = ZZ()) -> None:
        self.num = num
        self.denom = denom
        self.ring = ring
        if hasattr(ring, "gcd") and hasattr(ring, "ax_equals_b_find_x"):
            gcd = ring.gcd(self.num, self.denom) # type: ignore
            mu1 = ring.ax_equals_b_find_x(gcd, self.num) # type: ignore
            mu2 = ring.ax_equals_b_find_x(gcd, self.denom) # type: ignore
            self.num, self.denom = mu1, mu2

    @property
    def inv(self) -> Frac[T]:
        return Frac(self.denom, self.num)

    def __mul__(self, other: T | Frac[T]):
        if isinstance(other, Frac):
            if self.ring != other.ring:
                raise ValueError(f"Cannot multiply two fractions living in different rings: {self.ring} vs {other.ring}")
            return Frac(self.ring.multiply(self.num, other.num), self.ring.multiply(self.denom, other.denom))
        else:
            return Frac(self.ring.multiply(other, self.num), self.denom)

    def __rmul__(self, other):
        return self * other

    def __add__(self, other):
        if isinstance(other, Frac):
            if self.ring != other.ring:
                raise ValueError(f"Cannot multiply two fractions living in different rings: {self.ring} vs {other.ring}")
            num = self.ring.add(self.ring.multiply(self.num, other.denom), self.ring.multiply(self.denom, other.num))
            return Frac(num, self.denom * other.denom)
        else: # other has to be of type T
            other_frac = Frac(other, self.ring.one)
            num = self.ring.add(self.ring.multiply(self.num, other.denom), self.ring.multiply(self.denom, other.num))
            return Frac(num, self.denom * other.denom)


    def __radd__(self, other):
        return self + other

    def __repr__(self) -> str:
        if self.denom == self.ring.one:
            return str(self.num)
        return f"({self.num}/{self.denom})"

# class MultiplicativeSet[UnitaryRing[T]]:
#     class NotValidMultSet(ValueError):
#         pass
#     def __init__(self, _set: Set[T]) -> None:
#         self.check_multiplicativity(_set)
#         self.set = _set

#     def check_multiplicativity(self, s: Set[T]):
#         for e1 in s:
#             for e2 in s:
#                 if 

class Localization[T](UnitaryRing[T]):
    def __init__(self, r: UnitaryRing[T], i: Ideal[T]) -> None:
        if i.ring != r:
            raise ValueError(f"Ideal {i} must be an ideal of the ring {r}")
        self.ring = r
        self.ideal = i

    def validate_element(self, frac: Frac[T]) -> None:
        """Ensure the fraction's denominator is in the multiplicative set (not in the ideal)."""
        if frac.denom in self.ideal:
            raise ValueError(f"Denominator {frac.denom} is in the ideal {self.ideal}; it is not invertible in this localization.")

    def add(self, e1: Frac[T], e2: Frac[T]) -> Frac[T]:
        return e1 + e2

    def multiply(self, e1: Frac[T], e2: Frac[T]) -> Frac[T]:
        return e1 * e2

    def typst_str(self) -> str:
        return f"{self.ring.typst_str()}_({self.ideal.typst_str()})"

    def __repr__(self) -> str:
        return f"{self.ring}_({self.ideal})"

class QQ(UnitaryRing):
    """The ring of rational numbers"""
    def __init__(self) -> None:
        self.zero:      Frac[int]       = Frac(0, 1)
        self.one:       Frac[int]       = Frac(1, 1)

    def add(self, e1: Any, e2: Any) -> Any:
        return e1 + e2

    def mult_inv(self, e1: Frac[int]) -> Any | None:
        return 

    def __repr__(self) -> str:
        return "QQ"

class PolyRing[CoeffT](UnitaryRing[Polynomial[CoeffT]]):
    """
    The ring of polynomials R[x] over a given coefficient ring R.
    It is itself a UnitaryRing whose elements are Polynomial[T] instances.
    """
    def __init__(self, coefficient_ring: UnitaryRing[CoeffT]) -> None:
        self.coefficient_ring = coefficient_ring
        # Zero polynomial: 0 * x^0
        self.zero = Polynomial({0: coefficient_ring.zero}, coefficient_ring)
        # Unit polynomial: 1 * x^0
        self.one = Polynomial({0: coefficient_ring.one}, coefficient_ring)
        self.generators = None # we'd need infinitely many

    def is_finite(self):
        return False

    def validate(self) -> None:
        # Infinite structure, skip finite axiom checks
        pass

    def mult_inv(self, e1: Polynomial[CoeffT]) -> Polynomial[CoeffT] | None:
        if e1.is_zero or e1.deg > 0:
            print(f"The only units of a polynomial ring are the units of its ring, so {e1} is not invertible")
            return None
        inv = self.coefficient_ring.mult_inv(e1.coefficients[0])
        if inv is None:
            return None
        return Monomial[CoeffT](inv, 0, self.coefficient_ring)

    def add(self, p1: Polynomial[CoeffT], p2: Polynomial[CoeffT]) -> Polynomial[CoeffT]:
        return p1 + p2

    def multiply(self, p1: Polynomial[CoeffT], p2: Polynomial[CoeffT]) -> Polynomial[CoeffT]:
        return p1 * p2

    def typst_str(self) -> str:
        return f"{self.coefficient_ring.typst_str()} [x]"

    def __repr__(self) -> str:
        return f"{self.coefficient_ring}[x]"

class PolyRingQuot[T](PolyRing[T]):
    def __init__(self, coefficient_ring: UnitaryRing[T], ideal: PrincipalIdeal[MonicPolynomial[T]]) -> None:
        super().__init__(coefficient_ring)
        self.ideal = ideal
        min_deg = ideal.generator.deg
        self.generators = { Polynomial[T]({ power: coefficient_ring.one }, coefficient_ring) for power in range(min_deg) }

    def reduce_poly_mod(self, polynomial: Polynomial[T]) -> None:
        """Reduces the polynomial (in place)"""
        polynomial = polynomial.reduce_mod(self.ideal.generator)

    def mult_inv(self, e1: Polynomial[T]) -> Polynomial[T] | None:
        return NotImplemented # TODO

    def typst_str(self) -> str:
        return f"{self.coefficient_ring.typst_str()} [x] / ({self.ideal.generator.typst_str()})"

if __name__ == "__main__":
    coeff_r = ZZn(2)
    r = PolyRing[int](coeff_r)
    print(r.typst_str())
    i = PrincipalPolyIdeal(Monomial[int](1, 1, coeff_r), r)
    print(i.typst_str())
    print(i.is_prime())
    loc = Localization[Polynomial[int]](r, i)
    print(loc.typst_str())

    # import time

    # # A simple helper context manager for timing
    # class Timer:
    #     def __init__(self, name: str):
    #         self.name = name
    #     def __enter__(self):
    #         self.start = time.perf_counter()
    #         return self
    #     def __exit__(self, *args):
    #         self.end = time.perf_counter()
    #         print(f"[{self.name}] took {(self.end - self.start) * 1000:.4f} ms")

    # # Apply it to your operations:
    # with Timer("Ring Creation"):
    #     coeff_r = ZZn(2)
    #     r = PolyRing[int](coeff_r)

    # with Timer("Typst String Generation (Ring)"):
    #     print(r.typst_str())

    # with Timer("Ideal Creation"):
    #     i = PrincipalPolyIdeal(Monomial[int](1, 1, coeff_r), r)

    # with Timer("Typst String Generation (Ideal)"):
    #     print(i.typst_str())

    # with Timer("Prime Check (SymPy bridge)"):
    #     print(i.is_prime())

    # with Timer("Localization Creation"):
    #     loc = Localization[Polynomial[int]](r, i)

    # with Timer("Typst String Generation (Localization)"):
    #     print(loc.typst_str())

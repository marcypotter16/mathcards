
from random import choice, randint
import traceback
from typing import Any, Callable, Set, SupportsIndex
from sympy import Poly, invert
from sympy.abc import x

from math import gcd, lcm
from mathematics.base import Ideal, PrincipalIdeal, CommUnitRing, factorize, is_prime
from mathematics.poly import Polynomial


class ZZ(CommUnitRing):
    """The ring of integers"""
    _instance: "ZZ | None" = None

    def __new__(cls) -> "ZZ":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
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

    def neg(self, e):
        return -e

    def multiply(self, e1, e2):
        return e1 * e2

    def pow(self, e1: Any, exp: int) -> Any:
        return pow(e1, exp)

    def is_field(self) -> bool:
        return False

    def is_domain(self) -> bool:
        return True

    @property
    def typst_str(self) -> str:
        return "ZZ"

    def gcd(self, *integers: SupportsIndex):
        return gcd(*integers)

    def lcm(self, *integers: SupportsIndex):
        return lcm(*integers)

    def get_random_element(self) -> int:
        return randint(1, 10)

    def divides(self, a: int, b: int) -> int | None:
        """Return b // a if a | b in ZZ, else None. Raises ZeroDivisionError if a == 0."""
        if a == 0:
            raise ZeroDivisionError("division by zero")
        q, r = divmod(b, a)
        return q if r == 0 else None

    def __repr__(self) -> str:
        return "ZZ"

    def __hash__(self) -> int:
        return hash("ZZ")

class ZZn(CommUnitRing):
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

    def is_domain(self) -> bool:
        return self.is_field()

    def add(self, e1, e2):
        return (e1 + e2) % self.n

    def multiply(self, e1, e2):
        return (e1 * e2) % self.n

    def pow(self, e1: Any, exp: int) -> Any:
        return pow(e1, exp, self.n)

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

    @property
    def typst_str(self) -> str:
        return f"ZZ_({self.n})"

    def get_random_element(self) -> int:
        return randint(1, 100) % self.n

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return f"ZZ/({self.n})"

    def __hash__(self) -> int:
        return hash(f"ZZ{self.n}")

class IntegerIdeal(PrincipalIdeal[int]):
    def __init__(self, generators: Set[int], ring: CommUnitRing[int]) -> None:
        self.generators = generators
        self.generator = gcd(*generators) if self.generators else 0
        super().__init__(self.generator, ring)

    def is_prime(self) -> bool:
        return is_prime(self.generator)

    def is_maximal(self) -> bool:
        return self.is_prime()

    def is_radical(self) -> bool:
        if self.generator == 0:
            return True
        factors = factorize(self.generator)
        return all(power == 1 for power in factors.values())

    def get_random_element(self) -> int:
        return randint(-100, 100) * self.generator

    def get_random_element_in_complementary(self) -> int:
        n = abs(self.generator)
        if n <= 1:
            raise ValueError("Complement is empty or undefined for this ideal.")

        base = randint(-50, 50) * n
        remainder = randint(1, n - 1)
        return base + remainder

    @property
    def typst_str(self) -> str:
        return f"({self.generator})"

    def __contains__(self, item):
        return item % self.generator == 0

class PrincipalPolyIdeal(PrincipalIdeal[Polynomial]):
    """An ideal generated by a single polynomial"""
    def __init__(self, generator: Polynomial, coeff_ring: CommUnitRing) -> None:
        self.generator = generator
        self.coefficient_ring = coeff_ring
        self.ring = PolyRing(self.coefficient_ring)

    def get_random_element(self) -> Polynomial:
        return Polynomial.create_random(self.coefficient_ring, deg=4) * self.generator

    def get_random_element_in_complementary(self) -> Polynomial:
        gen = self.generator
        if gen.is_zero:
            ... # handle zero case
        if gen.deg == 0 and self.ring.is_invertible(gen.coefficients[0]):
            raise ValueError("Complement is empty (ideal is the whole ring).")

        # 1. Pick a random multiple q * gen
        def choose_deg(max: int = 2):
            return choice(range(max+1))
        q = Polynomial.create_random(self.coefficient_ring, deg=choose_deg())
        base = q * gen

        # 2. Add a random non-zero remainder r with degree < gen.degree
        # (If gen is degree 3, remainder can be degree 0, 1, or 2)
        remainder = Polynomial.create_random(self.coefficient_ring, deg=choose_deg(gen.deg - 1))
        
        # Ensure remainder is not zero
        while remainder.is_zero:
            remainder = Polynomial.create_random(self.coefficient_ring, deg=choose_deg())

        return base + remainder

    def __contains__(self, item):
        return item // self.generator == Polynomial.zero(self.ring)

    def is_prime(self) -> bool:
        print(f"Testing {self.generator}, {self.ring.typst_str}")
        if self.generator.is_zero:
            return True
        if isinstance(self.coefficient_ring, ZZ) or isinstance(self.coefficient_ring, QQ):
            p = self.generator.to_sympy(modulus=None)
            print(p)
            return p.is_irreducible
        if isinstance(self.coefficient_ring, ZZn):
            p = self.generator.to_sympy(modulus=self.coefficient_ring.n)
            print(p)
            return p.is_irreducible
        raise NotImplemented

    def is_maximal(self) -> bool:
        # TODO is this true?
        return self.is_prime()

class Frac[T]: 
    def __init__(self, num: T, denom: T, ring: CommUnitRing[T] = ZZ()) -> None:
        self.num = num
        self.denom = denom
        if self.denom == ring.zero:
            raise ZeroDivisionError
        self.ring = ring
        if hasattr(ring, "gcd") and hasattr(ring, "divides") and not self.num == self.ring.zero:
            gcd = ring.gcd(self.num, self.denom) # type: ignore
            mu1 = ring.divides(gcd, self.num) # type: ignore
            mu2 = ring.divides(gcd, self.denom) # type: ignore
            assert mu1 is not None and mu2 is not None # (they shouldn't be)
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

    def __neg__(self):
        return Frac(self.ring.neg(self.num), self.ring.neg(self.denom))

    def __sub__(self, other):
        return self + (-other)

    def __repr__(self) -> str:
        if self.num == self.ring.zero:
            return str(self.ring.zero)
        if self.denom == self.ring.one:
            return str(self.num)
        return f"(({self.num})/({self.denom}))"

    @property
    def typst_str(self) -> str:
        if hasattr(self.num, "typst_str") and hasattr(self.denom, "typst_str"):
            if self.denom != self.ring.one and self.num != self.ring.zero:
                return f"frac({self.num.typst_str},{self.denom.typst_str})" # type: ignore
            return self.num.typst_str # type: ignore
        if self.denom != self.ring.one and self.num != self.ring.zero:
            return f"frac({self.num},{self.denom})"
        return str(self.num)

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

class Localization[T](CommUnitRing[T]):
    def __init__(self, r: CommUnitRing[T], i: Ideal[T]) -> None:
        if i.ring != r:
            raise ValueError(f"Ideal {i} must be an ideal of the ring {r}")
        self.ring = r
        self.ideal = i

    def validate_element(self, frac: Frac[T]) -> None:
        """Ensure the fraction's denominator is in the multiplicative set (not in the ideal)."""
        if frac.denom in self.ideal:
            raise ValueError(f"Denominator {frac.denom} is in the ideal {self.ideal}; it is not invertible in this localization.")

    def get_random_element(self) -> Frac[T]:
        num = self.ring.get_random_element()
        den = self.ideal.get_random_element_in_complementary()
        return Frac(num, den)

    def add(self, e1: Frac[T], e2: Frac[T]) -> Frac[T]:
        return e1 + e2

    def multiply(self, e1: Frac[T], e2: Frac[T]) -> Frac[T]:
        return e1 * e2

    @property
    def typst_str(self) -> str:
        return f"{self.ring.typst_str}_({self.ideal.typst_str})"

    def __repr__(self) -> str:
        return f"{self.ring}_({self.ideal})"

class FractionField(Localization):
    def __init__(self, r: CommUnitRing) -> None:
        if not r.is_domain():
            raise ValueError(f"Can't create fraction field of a non domain ({r})")
        i = PrincipalIdeal(r.zero, r)
        super().__init__(r, i)

    @property
    def typst_str(self) -> str:
        return f"\"Frac\"({self.ring})"

    def __repr__(self) -> str:
        return f"Frac({self.ring})"


class QQ(CommUnitRing):
    """The field of rational numbers"""
    _instance: "QQ | None" = None
    def __new__(cls) -> "QQ":
        if cls._instance is None:
            _instance = super().__new__(cls)
        return _instance
    
    def __init__(self) -> None:
        self.zero:      Frac[int]       = Frac(0, 1)
        self.one:       Frac[int]       = Frac(1, 1)

    def add(self, e1: Any, e2: Any) -> Any:
        return e1 + e2

    def multiply(self, e1: Any, e2: Any) -> Any:
        return e1 * e2

    def sub(self, e1: Any, e2: Any):
        return e1 - e2

    def neg(self, e1: Any) -> Any:
        return -e1

    def get_random_element(self) -> Frac[int]:
        num = randint(0, 100)
        den = randint(1, 100)
        fra = Frac(num, den)
        return fra

    def is_finite(self) -> bool:
        return False

    def is_field(self) -> bool:
        return True

    def is_domain(self) -> bool:
        return True

    def mult_inv(self, e1: Frac[int]) -> Any | None:
        return e1.inv

    def __repr__(self) -> str:
        return "QQ"

    @property
    def typst_str(self) -> str:
        return "QQ"

    def __hash__(self) -> int:
        return hash("QQ")

class PolyRing[CoeffT](CommUnitRing[Polynomial[CoeffT]]):
    """
    The ring of polynomials R[x] over a given coefficient ring R.
    It is itself a UnitaryRing whose elements are Polynomial[T] instances.
    """
    def __init__(self, coefficient_ring: CommUnitRing[CoeffT]) -> None:
        self.coefficient_ring = coefficient_ring
        # Zero polynomial: 0 * x^0
        self.zero = Polynomial.zero(coefficient_ring)
        # Unit polynomial: 1 * x^0
        self.one = Polynomial({0: coefficient_ring.one}, coefficient_ring)
        self.generators = None # we'd need infinitely many

    def is_finite(self):
        return False

    def validate(self) -> None:
        # Infinite structure, skip finite axiom checks
        pass

    def get_random_element(self) -> Polynomial[CoeffT]:
        return Polynomial.create_random(self.coefficient_ring)

    def mult_inv(self, e1: Polynomial[CoeffT]) -> Polynomial[CoeffT] | None:
        if e1.is_zero or e1.deg > 0:
            print(f"The only units of a polynomial ring are the units of its ring, so {e1} is not invertible")
            return None
        inv = self.coefficient_ring.mult_inv(e1.coefficients[0])
        if inv is None:
            return None
        return Polynomial.monomial(inv, 0, self.coefficient_ring)

    def add(self, p1: Polynomial[CoeffT], p2: Polynomial[CoeffT]) -> Polynomial[CoeffT]:
        return p1 + p2

    def multiply(self, p1: Polynomial[CoeffT], p2: Polynomial[CoeffT]) -> Polynomial[CoeffT]:
        return p1 * p2

    @property
    def typst_str(self) -> str:
        return f"{self.coefficient_ring.typst_str} [x]"

    def __repr__(self) -> str:
        return f"{self.coefficient_ring}[x]"

class RingQuot(CommUnitRing):
    ring:       CommUnitRing
    ideal:      PrincipalIdeal

    def __init__(self, r: CommUnitRing, i: PrincipalIdeal) -> None:
        self.ring   = r
        self.ideal  = i

    @property
    def typst_str(self) -> str:
        return f"frac({self.ring.typst_str}, {self.ideal.typst_str})"

    def __repr__(self) -> str:
        return f"{self.ring}/{self.ideal}"

class PolyRingQuot[T](PolyRing[T], RingQuot):
    """Quotient of a ring of polynomials. The ideal should be generated by monic polynomials"""
    def __init__(self, coefficient_ring: CommUnitRing[T], ideal: PrincipalPolyIdeal) -> None:
        PolyRing.__init__(self, coefficient_ring)
        self.ring = PolyRing(coefficient_ring)
        self.ideal = ideal
        min_deg = ideal.generator.deg
        self.generators = { Polynomial[T]({ power: coefficient_ring.one }, coefficient_ring) for power in range(min_deg) }

    def reduce_poly_mod(self, polynomial: Polynomial[T]) -> None:
        """Reduces the polynomial (in place)"""
        polynomial = polynomial.reduce_mod(self.ideal.generator)

    def is_field(self) -> bool:
        return self.ideal.is_maximal()

    def get_random_element(self) -> Polynomial:
        return Polynomial.create_random(self.coefficient_ring, deg=4).reduce_mod(self.ideal.generator)

    def mult_inv(self, e1: Polynomial[T]) -> Polynomial[T] | None:
        p       = e1.to_sympy()
        mod     = self.ideal.generator.to_sympy()
        try:
            dom = 'ZZ'
            match self.coefficient_ring:
                case ZZ() | QQ():
                    dom = 'ZZ'
                case ZZn():
                    dom = f'GF({self.coefficient_ring.n})'
                case _:
                    dom = 'ZZ'                
            p_inv = invert(p, mod, domain=dom)
            return p_inv
        except ValueError:
            print(f"Warning: poly {e1} has no inverse modulo {mod}")
            return None

    @property
    def typst_str(self) -> str:
        return f"frac({self.coefficient_ring.typst_str}[x], {self.ideal.typst_str})"
    
    def __repr__(self) -> str:
        return f"({self.coefficient_ring}[x])/({self.ideal.generator})"

def find_irred_poly_in_ZZp(p: int, deg: int) -> Polynomial:
    """Implemented for p < 20, deg <= 3"""
    r = ZZn(p)
    
    # Degree 1 polynomials are always irreducible
    if deg == 1:
        return Polynomial.create_random(r, deg)

    poly = Polynomial.create_random(r, deg)
    
    def test_roots(poly, p) -> bool:
        for num in range(p):
            if poly.evaluate(num) % p == 0:
                return False
        return True

    is_irred = test_roots(poly, p)
    while not is_irred:
        poly = Polynomial.create_random(r, deg)
        print(poly)
        is_irred = test_roots(poly, p)
        
    return poly

class FFq(PolyRingQuot):
    def __init__(self, q: int) -> None:
        f = factorize(q)
        if len(f) != 1:
            raise ValueError("Finite fields should have cardinality q = p^e")
        self.q = q
        self.p = list(f.keys())[0]
        self.e = f[self.p]
        if self.p >= 20 or self.e > 3:
            raise NotImplementedError("Finite fields implemented only up to p=19, e=3")
        self.Fp = ZZn(self.p)
        self.ideal = PrincipalIdeal(find_irred_poly_in_ZZp(self.p, self.e), self.Fp)

    def is_field(self) -> bool:
        return True

    def is_domain(self) -> bool:
        return True

    @property
    def typst_str(self) -> str:
        return f"FF_{self.q}"

    def __repr__(self) -> str:
        return f"FF_{self.q}"


if __name__ == "__main__":
    z = ZZ()
    z1 = ZZ()
    z2 = ZZ()
    print(id(z) == id(z1), id(z2)) # ok they =
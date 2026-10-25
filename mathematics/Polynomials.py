import math
from typing import Callable, Dict, List
from sympy import Poly
from sympy.abc import x

from mathematics.Math import UnitaryRing


class Polynomial[T]:
    def __init__(self, coefficients: Dict[int, T], ring: UnitaryRing[T]) -> None:
        self.ring = ring
        self.coefficients = coefficients
        if hasattr(ring, "reduce_mod"):
            self.coefficients = {p: ring.reduce_mod(c) for p, c in self.coefficients.items()} # type: ignore
        self._normalize()
        # CONVENTION: negative degree is -infinity
        self.deg:           int         = max(self.coefficients.keys()) if self.coefficients else -1

    def _normalize(self) -> None:
        """Remove terms whose coefficients equal the ring's zero element."""
        self.coefficients = {p: c for p, c in self.coefficients.items() if c != self.ring.zero}

    @property
    def is_monic(self) -> bool:
        return self.LC == self.ring.one

    @property
    def is_monomial(self) -> bool:
        return self == self.LM

    @property
    def LC(self) -> T:
        """The leading coefficient (e.g. LC(3x^2 + 2) = 3)"""
        return self.coefficients[self.deg]

    @property
    def LM(self) -> Monomial[T]:
        """The leading monomial (e.g. LM(3x^2 + 2) = 3x^2)"""
        return Monomial[T](self.coefficients[self.deg], self.deg, self.ring)

    @property
    def is_zero(self) -> bool:
        return self.coefficients == {}

    def to_sympy(self, modulus: int | None = None) -> Poly:
        """Bridges a custom Polynomial to a SymPy Poly object."""
        # Assuming self.coefficients is a list ordered from lowest to highest degree:
        # We reverse it to match SymPy's highest-to-lowest expectation.
        high_to_low_coeffs = list(reversed(self.coefficients))
        
        if modulus is not None:
            return Poly(high_to_low_coeffs, x, modulus=modulus)
        return Poly(high_to_low_coeffs, x)

    def divides(self, other: Polynomial[T]) -> bool:
        return other.reduce_mod(self).is_zero

    def reduce_mod(self, mod: Polynomial[T]) -> Polynomial[T]:
        """
        Reduces this polynomial modulo a divisor polynomial using 
        polynomial long division. Returns the remainder polynomial.
        """
        if not mod.coefficients:
            raise ZeroDivisionError("Cannot reduce modulo the 0 polynomial")

        rem = Polynomial[T](self.coefficients, self.ring)

        while True:
            val = self.ring.divides(mod.LC, rem.LC) # the number mod.LC / rem.LC if possible, else None
            if rem.is_zero or rem.deg < mod.deg:
                break
            if not val:
                raise ValueError(f"LC of modulus does not divide LC of dividend: {mod.LC} vs {rem.LC}")
            rem -= val * Monomial(self.ring.one, rem.deg - mod.deg, self.ring) * mod

        return rem

    def __add__(self, other: 'Polynomial[T]') -> 'Polynomial[T]':
        d = dict(self.coefficients)
        for p, c in other.coefficients.items():
            if p in d:
                # Delegate addition to the Ring!
                d[p] = self.ring.add(d[p], c)
            else:
                d[p] = c
                
        return Polynomial[T](d, self.ring)

    def __iadd__(self, other):
        return self + other

    def __mul__(self, other: object) -> 'Polynomial[T]':
        if isinstance(other, Polynomial):
            if self.ring != other.ring:
                raise ValueError("Cannot multiply polynomials from different rings.")
            
            # --- Standard Polynomial * Polynomial multiplication ---
            new_coeffs = {}
            for deg1, coeff1 in self.coefficients.items():
                for deg2, coeff2 in other.coefficients.items():
                    target_deg = deg1 + deg2
                    prod_val = self.ring.multiply(coeff1, coeff2)
                    
                    if prod_val != self.ring.zero:
                        current = new_coeffs.get(target_deg, self.ring.zero)
                        new_coeffs[target_deg] = self.ring.add(current, prod_val)
                        
            return Polynomial(new_coeffs, self.ring)
            
        else:
            # --- Polynomial * Scalar multiplication ---
            # Assume 'other' is an element of type T from self.ring
            new_coeffs = {}
            for deg, coeff in self.coefficients.items():
                scaled_val = self.ring.multiply(coeff, other) # type: ignore
                if scaled_val != self.ring.zero:
                    new_coeffs[deg] = scaled_val
                    
            return Polynomial(new_coeffs, self.ring)

    def __rmul__(self, other: object) -> 'Polynomial[T]':
        # Scalar * Polynomial (e.g., 3 * p)
        # Multiplication in coefficient rings is typically commutative for scalars,
        # so we can just delegate to __mul__.
        return self * other

    def __divmod__(self, other):
        return self.reduce_mod(other)

    def __neg__(self) -> 'Polynomial[T]':
        neg_coeff = { power: self.ring.neg(coeff) for power, coeff in self.coefficients.items() }
        return Polynomial[T](neg_coeff, self.ring)

    def __sub__(self, other: 'Polynomial[T]') -> 'Polynomial[T]':
        return self + (-other)

    def __isub__(self, other):
        return self - other

    def __imul__(self, other):
        return self * other

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Polynomial):
            return NotImplemented
        if self.ring != value.ring:
            print(f"The polynomials {self} and {value} have different coefficient rings ({self.ring} vs {value.ring})")
            return False
        return self.coefficients == value.coefficients

    def __hash__(self) -> int:
        # Dictionaries aren't hashable, so convert coefficients to a sorted tuple of items.
        # Include self.ring so polynomials in different rings don't collide.
        coef_tuple = tuple(sorted(self.coefficients.items()))
        return hash((coef_tuple, self.ring))

    def typst_str(self) -> str:
        """
        Returns a Typst math-mode representation of the polynomial 
        (e.g., 'x^2 + 3x + 1'), utilizing coeff.typst_str() if available.
        """
        if self.is_zero:
            return "0"
            
        sorted_degs = sorted(self.coefficients.keys(), reverse=True)
        parts = []
        
        for i, deg in enumerate(sorted_degs):
            coeff = self.coefficients[deg]
            c_str = coeff.typst_str() if hasattr(coeff, "typst_str") else str(coeff) # type: ignore
            
            # Format the variable part
            if deg == 0:
                var_part = ""
            elif deg == 1:
                var_part = "x"
            else:
                var_part = f"x^{deg}"
                
            # Handle coefficient special cases (e.g., omitting '1' or '-1' before variables)
            is_one = (coeff == self.ring.one)
            is_neg_one = hasattr(self.ring, "neg") and (coeff == self.ring.neg(self.ring.one))
            
            if deg > 0 and is_one:
                c_term = var_part
                is_negative = False
            elif deg > 0 and is_neg_one:
                c_term = var_part  # we'll handle the minus sign separately
                is_negative = True
            else:
                is_negative = c_str.startswith("-")
                abs_c_str = c_str[1:] if is_negative else c_str
                
                if var_part:
                    if abs_c_str == "1":
                        c_term = var_part
                    else:
                        c_term = f"{abs_c_str} {var_part}"
                else:
                    c_term = abs_c_str
                    
            # Assemble terms with proper spacing and signs
            if i == 0:
                if is_negative:
                    parts.append(f"-{c_term}")
                else:
                    parts.append(c_term)
            else:
                if is_negative:
                    parts.append(f"- {c_term}")
                else:
                    parts.append(f"+ {c_term}")
                    
        return " ".join(parts)
    
    @staticmethod
    def zero(ring: UnitaryRing) -> Polynomial:
        return Polynomial({}, ring)

    @staticmethod
    def univariate_from_string(s: str, coeff_parser: Callable[[str], T], ring: UnitaryRing[T]) -> Polynomial:
        """
        Parses a string representation of a univariate polynomial where coefficients 
        can be enclosed in parentheses (e.g., '(1 + y) * x^2 + 3 * x + (5)').
        Returns a dictionary mapping degree (int) to coefficient (T).
        """
        terms_dict = {}
        
        # Split the polynomial by '+' to get individual terms
        raw_terms = s.split("+")
        
        for term in raw_terms:
            term = term.strip()
            if not term:
                continue
                
            # Check if there is a multiplication operator separating coefficient and x-part
            if "*" in term:
                # Split at the first '*'
                parts = term.split("*", 1)
                coeff_str = parts[0].strip()
                x_part = parts[1].strip()
            else:
                # If no '*', it's either just an x-term (like 'x^2' or 'x') or a pure coefficient
                if "x" in term:
                    coeff_str = "1"  # Implicit coefficient 1
                    x_part = term.strip()
                else:
                    coeff_str = term.strip()
                    x_part = ""
                    
            # Clean up outer parentheses from the coefficient string if present
            if coeff_str.startswith("(") and coeff_str.endswith(")"):
                coeff_str = coeff_str[1:-1].strip()
                
            # Evaluate the coefficient using the provided parser function/constructor
            coeff = coeff_parser(coeff_str)
            
            # Determine the degree of x
            if not x_part:
                degree = 0
            elif x_part == "x":
                degree = 1
            elif "^" in x_part:
                base, exp_str = x_part.split("^")
                degree = int(exp_str.strip())
            else:
                degree = 1
                
            terms_dict[degree] = coeff
            
        pol = Polynomial(terms_dict, ring)

        return pol

    def __repr__(self) -> str:
        if not self.coefficients:
            return "0"
            
        # Sort terms by degree in descending order (highest degree first)
        sorted_terms = sorted(self.coefficients.items(), key=lambda item: item[0], reverse=True)
        
        parts = []
        for deg, coeff in sorted_terms:
            if coeff == 0:
                continue
                
            # Format the monomial based on its degree
            if deg == 0:
                term_str = str(coeff)
            elif deg == 1:
                term_str = f"{coeff}*x"
            else:
                term_str = f"{coeff}*x^{deg}"
                
            parts.append(term_str)
            
        if not parts:
            return "0"
            
        # Join them cleanly and fix double signs (e.g., "+ -" becomes "- ")
        combined = " + ".join(parts)
        return combined.replace("+ -", "- ")


class MonicPolynomial[T](Polynomial[T]):
    class NotMonic(ValueError):
        pass
    def __init__(self, coefficients: Dict[int, T], ring: UnitaryRing[T]) -> None:
        super().__init__(coefficients, ring)
        if not self.is_monic:
            raise self.NotMonic(f"Polynomial {self} is not monic")

class Monomial[T](Polynomial[T]):
    class NotMonomial(ValueError):
        pass
    def __init__(self, coeff: T, power: int, ring: UnitaryRing[T]) -> None:
        super().__init__({ power: coeff }, ring)
        if not len(self.coefficients) <= 1:
            raise self.NotMonomial(f"Polynomial {self} is not a monomial")

if __name__ == "__main__":
    # Expression to parse
    expr = "(2) * x^2 + 3 * x + (5)"
    expr2 = "(4) * x^4 + (-1) * x^3 + (-5) * x + 2"

    # r = ZZn(2)

    # parsed_polynomial   = Polynomial.univariate_from_string(expr, lambda s: int(s), r)
    # pp2                 = Polynomial.univariate_from_string(expr2, lambda s: int(s), r)
    # print(parsed_polynomial)  # Output: {2: 2, 1: 3, 0: 5} representing 2x^2 + 3x + 5
    # print(pp2)
    # print(parsed_polynomial + pp2)
    # print(parsed_polynomial * pp2)
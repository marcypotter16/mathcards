from typing import Callable, Dict, List

from mathematics.Ring import ZZ, UnitaryRing, ZZn


class Polynomial[T]:
    def __init__(self, coefficients: Dict[int, T], ring: UnitaryRing[T]) -> None:
        self.ring = ring
        self.coefficients = coefficients
        if isinstance(ring, ZZn):
            self.coefficients = {p: ring.reduce_mod(c) for p, c in self.coefficients.items()}
        self._normalize()
        self.deg:           int         = max(self.coefficients.keys())

    def _normalize(self) -> None:
        """Remove terms whose coefficients equal the ring's zero element."""
        self.coefficients = {p: c for p, c in self.coefficients.items() if c != self.ring.zero}

    def __add__(self, other: 'Polynomial[T]') -> 'Polynomial[T]':
        d = dict(self.coefficients)
        for p, c in other.coefficients.items():
            if p in d:
                # Delegate addition to the Ring!
                d[p] = self.ring.add(d[p], c)
            else:
                d[p] = c
                
        return Polynomial[T](d, self.ring)

    def __mul__(self, other: 'Polynomial[T]') -> 'Polynomial[T]':
        d: Dict[int, T] = {}
        for power in range(self.deg + other.deg + 1):
            s = self.ring.zero
            # Include 'power' itself by using range(power + 1)
            for i in range(power + 1):
                j = power - i
                c1 = self.coefficients.get(i, self.ring.zero)
                c2 = other.coefficients.get(j, self.ring.zero)
                
                # Multiply coefficients, then add to the running sum
                term_product = self.ring.multiply(c1, c2)
                s = self.ring.add(s, term_product)
                
            if s != self.ring.zero:
                d[power] = s

        return Polynomial[T](d, self.ring)

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

if __name__ == "__main__":
    # Expression to parse
    expr = "(2) * x^2 + 3 * x + (5)"
    expr2 = "(4) * x^4 + (-1) * x^3 + (-5) * x + 2"

    r = ZZn(2)

    parsed_polynomial   = Polynomial.univariate_from_string(expr, lambda s: int(s), r)
    pp2                 = Polynomial.univariate_from_string(expr2, lambda s: int(s), r)
    print(parsed_polynomial)  # Output: {2: 2, 1: 3, 0: 5} representing 2x^2 + 3x + 5
    print(pp2)
    print(parsed_polynomial + pp2)
    print(parsed_polynomial * pp2)
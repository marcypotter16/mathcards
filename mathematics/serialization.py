# entities/mathematics/serialization.py

from typing import Any
from mathematics.base import CommUnitRing
from mathematics.poly import Polynomial
from mathematics.ring import QQ, ZZ, PolyRing, PolyRingQuot, Frac, PrincipalPolyIdeal, ZZn

# ---------- Elements ----------

def serialize_element(el: Any) -> dict[str, Any]:
    """Recursive element -> JSON-safe dict. Add a branch per element kind."""
    # ints first (covers ZZ and ZZn; ZZn elements are still Python ints)
    if isinstance(el, int):
        return {"kind": "int", "value": el}
    # fractions (QQ)
    if isinstance(el, Frac):
        return {
            "kind": "frac",
            "num": serialize_element(el.num),
            "den": serialize_element(el.denom),
        }
    # polynomials: dict power -> coeff, but pow is int-key
    if isinstance(el, Polynomial):          # adjust name
        return {
            "kind": "poly",
            "coeffs": [
                {"power": p, "coeff": serialize_element(c)}
                for p, c in el.coefficients.items()   # adjust attribute name
            ],
        }
    raise TypeError(f"serialize_element: unsupported element type {type(el).__name__}")


def deserialize_element(data: dict[str, Any], ring: CommUnitRing) -> Any:
    """Rebuild an element *inside a given ring* (ring needed for ZZn, polys, etc.)."""
    kind = data["kind"]
    if kind == "int":
        val = int(data["value"])
        if isinstance(ring, ZZ):
            return val
        if isinstance(ring, ZZn):
            return ring.reduce_mod(val)
        return val
        # return ring.coerce(data["value"])       # ZZn wraps mod n; ZZ passes through
    if kind == "frac":
        num = deserialize_element(data["num"], ring)
        den = deserialize_element(data["den"], ring)
        return Frac(num, den)   # or Fraction(num, den) for QQ
    if kind == "poly":
        coeffs = {
            entry["power"]: deserialize_element(entry["coeff"], ring)
            for entry in data["coeffs"]
        }
        if isinstance(ring, PolyRing):
            return Polynomial(coeffs, ring.coefficient_ring)        # ring knows how to build its elements
        return Polynomial(coeffs, ring)
    raise ValueError(f"deserialize_element: unknown kind {kind!r}")

# ---------- Rings ----------

def serialize_ring(ring: CommUnitRing) -> dict[str, Any]:
    if isinstance(ring, ZZ):    return {"kind": "ZZ"}
    if isinstance(ring, QQ):    return {"kind": "QQ"}
    if isinstance(ring, ZZn):   return {"kind": "ZZn", "n": ring.n}
    if isinstance(ring, PolyRingQuot):
        return {
            "kind": "polyring_quot",
            "coeff_ring": serialize_ring(ring.coefficient_ring),
            # "var":        ring.var,
            "var": "x",
            # modulus is an element of PolyRing(coeff_ring, var)
            "modulus":    serialize_element(ring.ideal.generator),
        }
    if isinstance(ring, PolyRing):
        return {
            "kind": "polyring",
            "coeff_ring": serialize_ring(ring.coefficient_ring),
            # "var":        ring.var,             # "x"
            "var": "x",
        }
    raise TypeError(f"serialize_ring: unsupported ring type {type(ring).__name__}")


def deserialize_ring(data: dict[str, Any]) -> CommUnitRing:
    kind = data["kind"]
    if kind == "ZZ":  return ZZ()
    if kind == "QQ":  return QQ()
    if kind == "ZZn": return ZZn(data["n"])
    if kind == "polyring":
        coeff = deserialize_ring(data["coeff_ring"])
        return PolyRing(coeff)
    if kind == "polyring_quot":
        coeff = deserialize_ring(data["coeff_ring"])
        base  = PolyRing(coeff)
        # deserialize the modulus element *inside* base
        modulus = deserialize_element(data["modulus"], base)
        return PolyRingQuot(coeff, PrincipalPolyIdeal(modulus, base))
    raise ValueError(f"deserialize_ring: unknown kind {kind!r}")


if __name__ == "__main__":
    def test_ring(ring):
        zser = serialize_ring(ring)
        print(ring)
        print(zser)
        print(deserialize_ring(zser), "\n")

    z = ZZ()
    test_ring(z)
    test_ring(QQ())
    test_ring(PolyRing(QQ()))
    q = QQ()
    test_ring(PolyRingQuot(q, PrincipalPolyIdeal(Polynomial.create_random(q, 2), q)))


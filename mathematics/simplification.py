from math import gcd

from mathematics.base import AdditiveGroup, Ideal, Morphism, PrincipalIdeal, CommUnitRing
from mathematics.poly import Polynomial
from mathematics.ring import QQ, ZZ, FFq, FractionField, IntegerIdeal, PolyRingQuot, PrincipalPolyIdeal, RingQuot, ZZn


class RingIsomorphismRegistry:
    # Class-level attribute: shared globally across the whole application
    _registry = []

    @classmethod
    def register(cls, condition_func, isomorphism_func):
        cls._registry.append((condition_func, isomorphism_func))

    @classmethod
    def simplify(cls, ring):
        for condition, target_func in cls._registry:
            if condition(ring):
                return target_func(ring)
        return ring

# Rule 1: Frac(ZZ) is isomorphic to QQ
RingIsomorphismRegistry.register(
    condition_func=lambda r: isinstance(r, FractionField) and isinstance(r.ring, ZZ),
    isomorphism_func=lambda r: QQ()
)

# Rule 2: Ring modulo (0) is isomorphic to the original ring
RingIsomorphismRegistry.register(
    condition_func=lambda r: isinstance(r, RingQuot) and r.ideal.generator == r.ring.zero,
    isomorphism_func=lambda r: r.ring
)

# Rule 3: Localization of a field at the zero ideal is the field itself
RingIsomorphismRegistry.register(
    condition_func=lambda r: isinstance(r, FractionField) and r.ring.is_field(),
    isomorphism_func=lambda r: r.ring
)

# Rule 4: FFp
RingIsomorphismRegistry.register(
    condition_func=lambda r: isinstance(r, PolyRingQuot) and not isinstance(r, FFq) and isinstance(r.coefficient_ring, ZZn) and r.is_field(),
    isomorphism_func=lambda r: FFq(r.coefficient_ring.n ** r.ideal.generator.deg)
)

# Rule 5: ZZn
RingIsomorphismRegistry.register(
    condition_func=lambda r: isinstance(r, RingQuot) and isinstance(r.ring, ZZ),
    isomorphism_func=lambda r: ZZn(gcd(*r.ideal.generators))
)

if __name__ == "__main__":
    r = ZZ()
    q = FractionField(r)
    red_q = RingIsomorphismRegistry.simplify(q)
    print(q, red_q)
    frac_q = FractionField(red_q)
    red_frac_q = RingIsomorphismRegistry.simplify(frac_q)
    print(frac_q, red_frac_q)
    q_mod = RingQuot(red_q, PrincipalIdeal(red_q.zero, red_q))
    red_q_mod = RingIsomorphismRegistry.simplify(q_mod)
    print(q_mod, red_q_mod)

    z2 = ZZn(2)
    f4_poly = PolyRingQuot(z2, PrincipalPolyIdeal(Polynomial({2: 1, 1: 1, 0: 1}, z2), z2))
    # print(isinstance(f4_poly.coefficient_ring, ZZn), f4_poly.is_field())
    f4 = RingIsomorphismRegistry.simplify(f4_poly)
    print(f4_poly, f4)

    zz = ZZ()
    i  = IntegerIdeal({12, 16, 24}, zz)
    qu = RingQuot(zz, i)
    zn = RingIsomorphismRegistry.simplify(qu)
    print(qu.typst_str, zn.typst_str)

from mathematics.base import Morphism
from mathematics.poly import Polynomial
from mathematics.ring import (
    ZZ,  # adjust imports to your layout
    Frac,
    LocalizationElement,
    PolyRing,
    ZZn,
)


def test_localization_element_validate():
    zx = PolyRing(ZZ())
    x = Polynomial({1: 1}, ZZ())          # x
    one = Polynomial({0: 1}, ZZ())        # 1
    two = Polynomial({0: 2}, ZZ())        # 2

    loc = LocalizationElement(zx, x)       # invert x

    # --- valid cases: denominator is a power of x (or 1) ---
    valid = [
        Frac(one, one, zx),                # 1/1
        Frac(two, one, zx),                # 2/1
        Frac(one, x, zx),                  # 1/x
        Frac(x, x, zx),                    # x/x
        Frac(two, x, zx),                  # 2/x
        Frac(one, x * x, zx),              # 1/x^2
        Frac(x, x ** 3, zx),               # x/x^3
        Frac(two, x ** 3, zx),             # 2/x^3
    ]
    for f in valid:
        assert loc.validate_element(f) is True, f"expected valid: {f!r}"

    # --- invalid cases: denominator has a factor that isn't x ---
    invalid = [
        Frac(one, two, zx),                # 1/2
        Frac(one, x + one, zx),            # 1/(x+1)
        Frac(one, x * two, zx),            # 1/(2x)
        Frac(one, x + two, zx),            # 1/(x+2)
        Frac(two, (x + one) * x, zx),      # 2/(x(x+1))
    ]
    for f in invalid:
        assert loc.validate_element(f) is False, f"expected invalid: {f!r}"

    zero = Polynomial.zero(ZZ())
    assert loc.validate_element(Frac(zero, x + one, zx)) is True, "0/(x+1) is fine"
    assert loc.validate_element(Frac(zero, x, zx)) is True,  "0/x is fine"

    assert loc.is_invertible(Frac(x, x, zx))     is True
    assert loc.is_invertible(Frac(two, x, zx))   is False
    assert loc.is_invertible(Frac(x**2, one, zx)) is True

    assert Frac(x, x, zx).denom == one
    # print(Frac(x, x**3, zx).denom, x * x)
    assert Frac(x, x**3, zx).denom == x * x

    print("All LocalizationElement.validate_element tests passed.")

def test_element_embedding():
    integers = ZZ()
    integers_mod_5 = ZZn(5)
    reduce_mod_5 = Morphism(integers, integers_mod_5, lambda value: value % 5)
    assert reduce_mod_5(7) == 2
    assert reduce_mod_5(-3) == 2

    integer_polynomials = PolyRing(integers)
    embed_as_constant = Morphism(
        integers,
        integer_polynomials,
        lambda value: Polynomial({0: value}, integers),
    )
    assert embed_as_constant(4) == Polynomial({0: 4}, integers)

    x = Polynomial({1: 1}, integers)
    one = Polynomial({0: 1}, integers)
    localization = LocalizationElement(integer_polynomials, x)
    assert localization.validate_element(Frac(one, x, integer_polynomials)) is True

if __name__ == "__main__":
    test_localization_element_validate()
    test_element_embedding()

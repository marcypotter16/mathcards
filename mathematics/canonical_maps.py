from collections.abc import Callable

from mathematics.base import CommUnitRing, Morphism
from mathematics.poly import Polynomial
from mathematics.ring import (
    QQ,
    ZZ,
    Frac,
    FractionField,
    LocalizationElement,
    LocalizationPrimeIdeal,
    PolyRing,
    ZZn,
)


class Conversion:
    _registry = []

    @classmethod
    def register(cls, 
                 condition: Callable[[CommUnitRing, CommUnitRing], bool], 
                 build_morphism: Callable[[CommUnitRing, CommUnitRing], Morphism]):
        cls._registry.append((condition, build_morphism))

    @classmethod
    def try_get(cls, 
                source: CommUnitRing, 
                target: CommUnitRing) -> Morphism | None:
        for condition, build_morphism in cls._registry:
            if condition(source, target):
                return build_morphism(source, target)
        return None


Conversion.register(
    condition=lambda source, target: isinstance(source, ZZ) and isinstance(target, ZZn),
    build_morphism=lambda source, target: Morphism(
        source,
        target,
        lambda value: value % target.n, # type: ignore
    ),
)

Conversion.register(
    condition=lambda source, target: isinstance(target, PolyRing) and source == target.coefficient_ring,
    build_morphism=lambda source, target: Morphism(
        source,
        target,
        lambda value: Polynomial({0: value}, source),
    )
)

Conversion.register(
    condition=lambda source, target: isinstance(target, 
                                                (LocalizationElement, 
                                                 LocalizationPrimeIdeal, 
                                                 FractionField)) 
                                                 and source == target.ring,
    build_morphism=lambda source, target: Morphism(
        source,
        target,
        lambda value: Frac(value, source.one, source),
    )
)

Conversion.register(
    condition=lambda source, target: isinstance(source, ZZ) and isinstance(target, QQ),
    build_morphism=lambda source, target: Morphism(
        source,
        target,
        lambda value: Frac(value, 1)
    )
)

if __name__ == "__main__":
    z = ZZ()
    zn = ZZn(5)
    mor = Conversion.try_get(z, zn)
    assert mor is not None
    print(mor(123))
    zx = PolyRing(z)
    embed = Conversion.try_get(z, zx)
    assert embed is not None
    print(embed(13))
    zxy = PolyRing(zx)
    embed2 = Conversion.try_get(zx, zxy)
    assert embed2 is not None
    print(embed2(Polynomial({1: 1}, zx))) # type: ignore

    x = Polynomial({1: 1}, z)
    one = Polynomial({0: 1}, z)
    localization = LocalizationElement(zx, x)
    localization_map = Conversion.try_get(zx, localization)
    assert localization_map is not None
    embedded_one = localization_map(one)
    embedded_x = localization_map(x)
    print(embedded_one)
    assert embedded_one == Frac(one, zx.one, zx)
    assert embedded_x == Frac(x, zx.one, zx)
    assert localization.validate_element(embedded_one)
    assert localization.validate_element(embedded_x)

    fraction_field = FractionField(zx)
    fraction_field_map = Conversion.try_get(zx, fraction_field)
    assert fraction_field_map is not None
    assert fraction_field_map(x) == Frac(x, zx.one, zx)

    assert Conversion.try_get(ZZ(), localization) is None

from mathematics.poly import Polynomial
from mathematics.ring import PolyRingQuot, PrincipalPolyIdeal, ZZn, find_irred_poly_in_ZZp

z2 = ZZn(2)
pol = find_irred_poly_in_ZZp(2, 2)
i = PrincipalPolyIdeal(pol, z2)
p = PolyRingQuot(z2, i)
print(p.is_field())
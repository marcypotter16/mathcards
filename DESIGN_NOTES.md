# Mathcards — Core Game Plan

## Central mechanic

Mathcards is a Cirulla-like game played over a mutable **active finite ring**. Cards carry familiar integer labels, but their current values are

\[
n_R = n \cdot 1_R,
\]

so changing the active ring immediately changes the hand and table. In `ZZ/5`, for example, `5` becomes zero and `2` and `7` become equal.

The main capture rule is zero-sum:

\[
c+x_1+\cdots+x_k=0_R.
\]

Cirulla is the motivating fixed-modulus case; Mathcards allows players to change the ambient ring and therefore the available zero-sum combinations.

## Ring changes and morphisms

- A ring change includes a unital homomorphism `φ: R → S` whenever existing constructed elements must be transported.
- Numeral cards need no stored element: they are reevaluated through the canonical map `ZZ → S`.
- General element cards are transported as `a ↦ φ(a)`; without a suitable map, they remain tied to their original ring.
- Homomorphisms preserve existing equations, but noninjective maps create new equations, collisions, and zeros. A quotient therefore adds capture possibilities rather than invalidating algebraic equalities.
- Mapping `1_R` to `1_S` is required but generally does not determine a homomorphism; generator images must also respect all relations.

Typical ring-change cards include `Reduce Modulo n`, `Quotient`, `Invert Element`, `Evaluate at a`, and `Pass to Endomorphisms` when a canonical map is available.

## Endomorphism rings

For the additive cyclic group `C_n = ZZ/(n)`,

\[
End_Ab(C_n) \cong ZZ/(n)
\]

through `f ↦ f([1])`; the inverse sends `[a]` to `x ↦ ax`. Endomorphism addition is pointwise and multiplication is composition. In the reverse direction, `[1]` maps to the identity endomorphism, so numeral cards remain meaningful.

Keep both the construction and any recognized model:

```text
Constructed as: End_Ab(C_n)
Recognized as:  ZZ/(n)
Isomorphism:    f ↦ f([1])
```

The cyclic case is special: for example, `End_Ab(C₂ × C₂) ≅ M₂(FF₂)`.

## Initial scope

- Small finite commutative rings, with an element-count cap.
- `ZZ/(n)`, finite fields, products, and low-degree `FF_p[x]/(f)`.
- The engine may enumerate elements to test units, zero divisors, nilpotents, field status, and zero-sum captures.
- Mathematical claims return a certificate or counterexample; otherwise their state is `unknown`.
- Strong players benefit from predicting structural changes, while beginners can experiment and learn from the engine's explanations.

## Rendering

- Python 3.14 with `pyray`; Raylib/GPU operations stay on the main thread.
- Typst renders formulas asynchronously to padded transparent PNGs.
- Cache textures by formula, style, PPI, and template version.
- Render for the largest planned card scale and downscale during animations.

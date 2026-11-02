Mathcards — Zero-Forging Core Design Notes

A consolidation of the design discussion: the zero-forging loop, explosions, the category system, ring changes, items, and the action economy. Written to be read before coding, and to be pruned as playtesting dictates.
0. The one-sentence core

Build a zero in a public shared cell; your opponent gets one turn to disturb it; cash it in at the start of your next turn if it survived. Everything else — explosions, category switches, ring changes, items — is a modifier on that loop.

If a rule does not make the build / threaten / defend / cash cycle more interesting, cut it.
1. The construction cell
1.1 Basic shape

    N slots (start with N = 3). A cell holds an ordered expression over the active ring.

    The cell's value is the expression's evaluation in the current ring. It is public — the whole interference game depends on the opponent seeing that you have a zero.

    One shared cell for v0. Multiple cells is a later layer.

1.2 Ownership

    A cell is owned by whoever last placed a card on it. Ownership transfers on opponent placement.

    Ownership determines: who can cash it in, who can sacrifice from it, and who pays penalties for explosions that occur in it.

    Rationale: this makes an attack that adds +1 to your zero cost the attacker — they've stolen a nearly-finished cell and must now rebuild it. Attacks are real trades, not free harassment.

1.3 Slot integrity

    The cell is a fixed-size expression: cards replace slots rather than being appended without bound. This keeps the arithmetic inspectable and prevents an attacker from burying a zero under noise.

    Heavy ring-changing attacks are the exception (§4).

2. The cash-in

    Cashing is free but must be your first action on your turn, and only if a cell you own evaluated to 0 at the start of the turn.

    The cell is consumed on cash-in (v0). A "persistent engine" variant is a v1 consideration.

    Why "first action" and not "costs an action": with a 3-action turn, a 1-action cash-in makes the cash turn a normal turn plus a payout, which kills the delay tension. Making it free-but-first preserves the tension while keeping the 3-action budget intact. The cost of cashing is the turn you spent building and the risk the opponent breaks it.

    Fallback tuning knob: if zeros cash too easily in playtesting, change to "cash-in costs 1 action and must be your first action." Start with free-first.

2.1 The delay

    The window is exactly one opponent turn. Not "any later turn."

    Rationale: an unbounded window lets a defender stall and lets an attacker wait for a convenient moment; a single opponent turn is legible, tense, and balances cleanly.

    If a longer window is ever wanted, make it a paid extension, not a default.

2.2 If the zero is broken

    Cash-in succeeds iff the cell is 0 at the moment you cash. If the opponent disturbed it, the cash simply fails; the cards stay on the table and you may rebuild.

    Breaking a zero therefore delays rather than cancels — unless the attacker uses a detonation (§3) that clears the cell entirely.

3. Explosions
3.1 The base rule

    Invert on a non-unit explodes. This is a single predicate (is_unit(a), already in the engine's enumeration toolset) and it is uniform across every ring.

    Pedagogical honesty: you attempted an illegal operation (inverting a non-unit); the game punishes you. This is the "fun rule" — one sentence, no per-ring exceptions.

3.2 Propagation (bounded)

    Same-cell recursion: the exploding card is removed; then every remaining non-unit in the same cell explodes, recursively, until no non-units remain.

    Cross-cell propagation is an item (Fuse), not a base rule. This keeps the base board state inspectable and makes the table-clearing bomb a deliberate, visible purchase.

    Caveat: in ZZ/6, most elements (2, 3, 4, 0) are non-units, so Invert is almost always an explosion. ZZ/6 is a volatile ring. Surface a per-ring "volatility" indicator in the UI. This is a feature, not a bug.

3.3 The trivial ring

    Exclude the zero ring {0} from the card pool. In it, 0 = 1 is a unit, so Invert(0) is legal and nothing explodes — a special case not worth carrying.

3.4 Explosions are Ring-only

    In Grp mode, Invert is the additive inverse, which exists for every element. Nothing explodes in Grp.

    Consequence: explosions are a multiplicative phenomenon. Switching to Grp disables explosions (and multiplicative forging) in exchange for universal invertibility. Switching to Ring enables both.

    This is the cleanest justification for the category system in the whole design. It is mathematically forced, mechanically legible, and gives the category switch a real tempo role (§5).

3.5 The Invert(0) detonation as a move

    Invert on a cell whose value is 0 is a legal attack: it clears the cell (all cards discarded) and costs the actor a penalty (1 action + discard a card from hand, say).

    Rationale: it gives the attacker a universal, expensive answer to any zero, which is exactly the pressure valve the interference game needs. It is also the second use of the same primitive — players will retell "I detonated his zero."

4. Ring changes and morphism transport

(You already have the morphism machinery; this section pins down its interaction with the cell.)
4.1 What a ring change does

    A ring-change effect card presents a unital homomorphism φ: R → S.

    Numerals auto-transport through the canonical ZZ → S; they are ring-change-proof and therefore the robust cards.

    General element cards become stale until transported. Transporting one costs an action (Transport).

    Zeros survive ring changes, because every unital hom preserves 0. The expression may change while the value stays 0 — the opponent cannot break a zero by ring-changing, only by perturbing the expression. Call this out in the tutorial.

4.2 Collisions are a tool

    When φ is non-injective, transported cards collide: 2 and 7 both become 2 under ZZ → ZZ/5.

    Merge collided cards — two cards equal in the new ring are the same card. The player now holds a pair of identical values, which is a zero-forging tool (a − a = 0).

    Rationale: this makes the design doc's promise — "noninjective maps create new equations" — mechanical. Lean into it.

4.3 Ring change as a tempo attack

    A ring change is both a board-state attack (every value shifts, possibly breaking or creating zeros) and a tempo attack (every non-numeral card must be re-transported).

    Make it rare and visible so the opponent can see it coming and play Anchor (§6).

5. The active category (Grp / Ring)

    Shared per table in v0 (not per-player). This makes the category a collective resource and gives Forget / Remember real drama.

    Grp mode: additive only. +, −, additive Invert (always exists). No multiplication, no explosions, no multiplicative zeros. Low-variance, grindy.

    Ring mode: adds · and multiplicative Invert (units only). Multiplicative forging, explosions, zero divisors. High-variance, dramatic.

    Switching is the game's tempo control: go to Grp to protect a zero (Invert becomes harmless); go to Ring to threaten with explosions.

    Reversibility: Forget to Group is cheap/free (forgetful functor — you lose info). Remember Ring Structure costs something (you assert structure) and is legal only when a recognized ring model exists on the object (your End_Ab(C_n) ≅ ZZ/(n) "Recognized as" pattern generalizes).

    v0 scope: only Grp and Ring. No Field / Alg/R / Mon yet.

6. Items (v1 — cut from v0)

Items are the money sink and the protect/attack layer. Two rules keep them healthy:

    Situational, not absolute. "This slot can't be inverted" is absolute and invites a breaker. Prefer "inverting this slot costs an extra action" or "the first explosion in this cell each turn is negated."

    Visible and timed. A face-up item with a duration creates a window to wait out or attack around. Hidden permanent shields feel unfair and break the public-information model.

6.1 Item sketches
Item	Effect	Role
Slot Shield	This cell cannot be targeted by Invert until your next turn.	Timed protection against detonation
Fuse	Your explosions propagate to adjacent cells this turn.	The table-clearing bomb; a visible threat
Filter	When a cell you own would explode, only one card is removed instead of all non-units.	Compositional defense
Anchor	This card's value ignores ring-change morphisms this turn.	Defense against the ring-change nuke
Chain Letter	Draw 2, discard 1.	Generic economy

None of these say "you can't do X at all" — each shifts a cost or narrows a window.
7. The turn

    3 actions. Choose among:

        Draw — draw 1 card.

        Play Element — place a ring-card in a cell you own (or create a cell).

        Play Effect — +, −, ·, Invert on any cell (explosion rule applies).

        Transport — apply the current φ to one stale card.

        Sacrifice — discard 2 cards from a cell you own → draw 1; or 3 → draw 2. Only from cells you own.

        Buy Item — spend money; items are visible and timed. (v1)

    Cash-in: free, but must be your first action on your turn, and only if a cell you own was 0 at the start of the turn. Cell is consumed.

7.1 Sacrifice

    Sacrifice from the playing field, not hand — the cost is visible, and it interacts with explosions (sacrificing a cell full of non-units is cheaper than it looks).

    Rates: 2 → 1 is the standard fallback; 3 → 2 is the "burn more field for a better rate" variant. The choice is how much of my field am I willing to burn.

    Ownership matters: you can only sacrifice from cells you own. This gives attacks a second consequence — they deny sacrifice fodder as well as breaking zeros.

7.2 On drawing too much

    Not a balance concern right now. Over-drawing is usually a tempo loss (you aren't playing cards), but it can be a powerful move: keep your cards hidden, let the opponent commit to the field, then attack from a large hand.

    No hand cap for now. Revisit only if playtesting shows draw-only turns dominating.

7.3 The action-budget invariant to test

    Can a player always break an exposed zero in one opponent turn?

    If yes, zeros never cash and the game stalls.

    If no, zeros always cash and defense is pointless.

    Tune the budget until the answer is "only if they have the right card" — i.e. attacks are conditional on hand, not always available.

8. How different rings play

Different rings are different games, not reskins. This is the argument for the whole ring machinery.
Ring	Character	Forging	Invert
ZZ/p (field)	Additive zeros dominate; every nonzero is a unit	Additive; x · 0 only multiplicatively	Always legal on nonzero — a strong defensive tool
ZZ/6 (zero divisors)	Volatile — most elements are non-units	2 · 3 = 0 gives multiplicative zeros	Usually an explosion; detonation is the main Invert
ZZ/p[x]/(f), f irreducible	Field; like ZZ/p	Additive	Always legal
ZZ/p[x]/(f), f reducible	Zero divisors from the factor structure	Multiplicative forging opens up	Often explosive
Ring change f irreducible → reducible	The big swing	Turns a field into a zero-divisor ring	Volatility jumps

Tutorial scenario: walk through ZZ/5 (field: additive zeros, invert as defense) vs ZZ/6 (zero divisors: multiplicative zeros, invert as detonation). The contrast alone justifies the ring system.
9. The ZZ/5 endomorphism teaching moment

The canonical first demonstration of the category axis:

    In Grp, Hom(ZZ/5, ZZ/5) ≅ ZZ/5 — 5 group endomorphisms (choose the image of the generator). Multiplication is off; Invert is additive and safe; no explosions.

    In Ring, the unital condition 1 ↦ 1 forces the only ring endomorphism to be the identity. But now multiplicative capture is on, 2 · 3 = 1 is live, and Invert on 0 detonates.

One table state demonstrates every axis: morphism count, gated multiplication, explosion availability, transport rules. Build the tutorial around it.
10. v0 scope cut

Ship this first; everything else is a layer.

Keep:

    One shared cell, N = 3 slots, ownership by last placer.

    Shared category: Grp / Ring.

    Cards: numerals (auto-transporting), +, −, ·, Invert, one ring-change card, one Forget/Remember pair.

    3 actions per turn; cash-in free-but-first.

    Explosion recursion, same-cell only.

    Ring-change morphism transport, stale cards, collisions merge.

    Sacrifice (2 → 1, 3 → 2), from owned cells only.

Cut from v0 (first expansion):

    Items — the category switch already provides protect/attack tension (Grp protects, Ring attacks).

    Cross-cell explosion propagation — same-cell recursion is dramatic enough and keeps the board inspectable.

    Multiple cells, per-cell categories, money, persistent-engine cash-in.

Testable in a weekend. Contains ~90% of the fun.
11. Open questions to resolve before coding

    Is the zero secret or public? This document assumes public (interference needs visibility). A bluffing variant — declare a hidden zero, opponent must guess — is a different game. Pick one; don't half-do it.

    Does cash-in consume the cards or free them? v0: consume. v1: consider a persistent cell with a cash fee (a reusable zero engine, with permanent interference as the counter).

    Category change ordering vs. ring change. If a player changes both in one turn, in which order, and must the morphism exist in source, target, or both categories? Suggested: the category-change card specifies the forgetful/forgetful-like functor; transport happens only along a morphism that exists in the target category.

    Stale-card revalidation. A card transported in Grp along a non-ring group hom is a valid group element but may not be a valid ring element (it may not respect multiplication). Proposed: store (value, transported_via: (category, morphism)) on each card; define capture/effect legality as "the card's transport category is at least as rich as the operation's required structure" — a small lattice Grp < Ring. Switching to a richer category does not retroactively validate old transports; the player must re-transport.

    Trivial-ring exclusion — confirm the zero ring is banned from the card pool (or special-cased).

12. The rules to write in bold before anything else

    Explosions are Ring-only, because additive inverses always exist.

    Zeros survive ring changes, because unital homs preserve 0.

    The cash window is exactly one opponent turn.

    Ownership transfers on placement.

These four sentences make the whole system coherent, and all four are mathematically forced. That is the best kind of rule.
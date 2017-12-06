

# Helter

## Syntax

A Helter expression is one of two things:
- A named reference, e.g. `foo` (containing any non-whitespace, non-reserved characters).
- A "chain" of "links"

Each link is a bracketed list of terms.

Brackets come from the following set: `()[]{}<>`

A term can either be:
 - An expression
 - An 'indexed' expression consisting of a reference name and an expression separated by `:`

The behavior of a link is determined by the type of bracket at each of its ends.

Brackets _need not have matching types_.

Each link or chain acts as a component in a data stream. The output of the expression to a link's left is fed into it, and its output is then passed on to the link on its right.

Each of the brackets have the following effects on link semantics:

`x (y, z` | the output of `x` becomes the input to each of `y` and `z`

`y, z) w` | the output of `z` becomes the input to `w`

`x {y, z` | the first component of the construct `x` becomes the input to `y`, and the second component becomes the input to `z`

`y, z} w` | `y` and `z` become the first and second components of a structure that then becomes the input to `w`

`[y` | regardless of its input, the rest of the chain containing this link is severed and becomes the output of the expression containing it

`x: y] z` | `z` is evaluated in a scope containing a reference with key `x` and value `y`

`x <y, z` | the first and second "adjuncts" of `x` become the inputs to `y` and `z` respectively

`y, z> w` | the input to `w` is the value that was the input to the link containing `y` and `z`, but with `y` and `z` as its first and second adjunct values (assuming they are the only terms in the link)

Each term following `{` or `<` or preceding `}` or `>` may be an indexed expression, in which case the component or adjunct values are accessed by keyword instead of by order alone.

If a link in a chain is a reference, and that reference evaluates to a severed chain, the severed chain is inserted into the chain being evaluated (but as a closure, preserving its original scope).
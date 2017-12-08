

# Helter
### An esoteric programming language built on mismatched braces

## Syntax

A Helter expression is one the following:
- A literal (integer, decimal, or string)
- A named reference, e.g. `foo` (containing any non-whitespace, non-reserved characters).
- A link
- A chain of multiple expressions

Each link is a bracketed, comma-separated list of terms.

Brackets come from the following set: `()[]{}<>`

A term can either be:
 - An expression
 - An input key and an expression, separated by `:`
 - An input key, an expression, and an output key, separated by `:`
In the latter two cases, the keys may be left blank, in which case matching is performed by position,
and the expression may be empty.

Each link or chain acts as a component in a data stream. The output of the expression to a link's left is fed into it, and its output is then passed on to the expression on its right.

The behavior of a link is determined by the type of bracket at each of its ends.

Brackets do **not** need to have matching types.

Each of the brackets have the following effects on link semantics:

`x (y, z` | the output of `x` becomes the input to each of `y` and `z`

`y, z) w` | the output of `z` becomes the input to `w`

`x {y, z` | the first component of the construct `x` becomes the input to `y`, and the second component becomes the input to `z`

`y, z} w` | `y` and `z` become the first and second components of a structure that then becomes the input to `w`

`[y` | regardless of its input, the rest of the chain containing this link is severed and becomes the output of the expression containing it, with this brace replaced by `(`

`:y:x] z` | `z` is evaluated in a scope containing a reference with key `x` and value `y`

`x <y, z` | the first and second "adjuncts" of `x` become the inputs to `y` and `z` respectively

`y, z> w` | the input to `w` is the value that was the input to the link containing `y` and `z`, but with `y` and `z` as its first and second adjunct values (assuming they are the only terms in the link)

Each term following `{` or `<` may have specified input keys, and those preceding `}` or `>` may have specified output keys. In these cases, component or adjunct values are accessed by name instead of by position.

Terms preceding `]` must have specified output keys in order to produce references in the following scope.

If a link in a chain is a reference, and that reference evaluates to a severed chain, the severed chain is inserted into the chain being evaluated (but as a closure, preserving its original scope).

## Using Helter

Invoke the interactive shell with either of the following commands:

```
$ python3 -m repl
$ python3 -m helter
```

A prompt should appear. You can type helter expressions into this prompt as part of an ongoing chain and view the intermediate values.

```
> (:[>:id]
()
```
Evaluating this expression introduced a binding for the reference `id` to the chain `(>`.
The immediate result was the "unit" value, indicated by `()`.

Now we can refer to the chain `(>` by the handy name `id`:
```
> 1 (>
1
> 1 id
1
```
`id` is a chain that returns whatever its input is.

Type `:q` to exit the repl.

The following references are defined by default:

`unit`: the unit value

`true` and `false`: boolean values

`!`: negation operator (defined for booleans)

`&`, `|`: boolean arithmetic operators (defined for booleans)

`=`: equality operator (defined for booleans, integers and strings)

`+`: addition/concatenation operator (defined for integers and strings)

`-`, `*`, `/`, `%`: arithmetic operators (defined for integers and floats)

`<`, `>` : strict ordering operators (defined for integers and floats)

`<=`, `>=`: or-equal-to ordering operators (defined for integers)

`length`: length operator (defined for strings)

Binary operators accept their input values as a two-place structure:
```
> (2, 3} +
5
```


class SymbolPool:
    def __init__(self):
        self.data = {}
    def __getitem__(self, k):
        return self.data.get(k) or self.make(k)
    def get(self, k, default=None):
        return self.data.get(k) or self.make(k)
    def __contains__(self, k):
        return True
    def make(self, k):
        s = Symbol(k)
        self.data[k] = s
        return s

class Scope(dict):
    def __init__(self, base):
        super().__init__()
        self.base = base
    def __getitem__(self, k):
        return super().get(k) or self.base[k]
    def get(self, k, default=None):
        return super().get(k) or self.base.get(k, default)
    def __contains__(self, k):
        return k in self or k in self.base
    def __repr__(self):
        return '%s + %s' % (repr(self.base), super().__repr__())

class Protect:
    def __init__(self, base):
        self.base = base
    def __getitem__(self, k):
        return self.base[k]
    def get(self, k, default=None):
        return self.base.get(k, default)
    def __contains__(self, k):
        return k in self.base
    def __setitem__(self, k, v):
        pass
    def __repr__(self):
        return 'Protect(%s)' % repr(self.base)

class Shadow:
    def __init__(self, base, shadow_keys):
        self.base = base
        self.shadow_keys = shadow_keys
    def __getitem__(self, k):
        if k in self.shadow_keys:
            raise IndexError()
        else:
            return self.base[k]
    def get(self, k, default=None):
        return default if k in self.shadow_keys else self.base.get(k, default)
    def __contains__(self, k):
        return k not in self.shadow_keys and k in self.base

class Value:
    def __init__(self, adjuncts=None):
        self.adjuncts = adjuncts or {}
    def get_adjunct(self, index):
        return self.adjuncts.get(index, HNONE)
    def get_component(self, index):
        return HNONE
    def adjoin(self, d):
        updated = dict(d)
        for k, v in self.adjuncts.items():
            if k not in updated:
                updated[k] = v
        return Value(updated)

class Boxed(Value):
    def __init__(self, content, adjuncts=None):
        super().__init__(adjuncts)
        self.content = content
    def adjoin(self, d):
        updated = dict(d)
        for k, v in self.adjuncts.items():
            if k not in updated:
                updated[k] = v
        return Boxed(self.content, updated)
    def __str__(self):
        return repr(self.content)

class Symbol(Value):
    def __init__(self, name, adjuncts=None):
        super().__init__(adjuncts)
        self.name = name
    def adjoin(self, d):
        updated = dict(d)
        for k, v in self.adjuncts.items():
            if k not in updated:
                updated[k] = v
        return Symbol(self.name, updated)
    def __str__(self):
        return self.name

class HelterNone(Value):
    def __init__(self):
        pass
    def get_adjunct(self, index):
        return self
    def get_component(self, index):
        return self
    def adjoin(self, d):
        return self
    def __str__(self):
        return '()'

HNONE = HelterNone()

class Struct(Value):
    def __init__(self, data, adjuncts=None):
        super().__init__(adjuncts)
        self.data = data
    def get_component(self, index):
        return self.data.get(index, HNONE)
    def adjoin(self, d):
        updated = dict(d)
        for k, v in self.adjuncts.items():
            if k not in updated:
                updated[k] = v
        return Struct(self.data, updated)
    def __str__(self):
        if all(isinstance(k, int) for k in self.data):
            return '(%s}' % ', '.join(str(self.data[i]) for i in range(len(self.data)))
        return '(%s}' % ', '.join(':%s:%s' % (str(val), key) for key, val in self.data.items())
    def __eq__(self, other):
        return isinstance(other, Struct) and self.data == other.data

class FloatingChain(Value):
    def __init__(self, chain, saved_scope=None, adjuncts=None):
        super().__init__(adjuncts)
        self.chain = chain.subst(saved_scope) if saved_scope is not None else chain
    def adjoin(self, d):
        updated = dict(d)
        for k, v in self.adjuncts.items():
            if k not in updated:
                updated[k] = v
        return FloatingChain(self.chain, updated)
    def __str__(self):
        return str(self.chain)

class Expression:
    def evaluate(self, inputs, scope, mutate_scope=False):
        raise NotImplementedError()
    def subst(self, scope):
        raise NotImplementedError()

class Identity(Expression):
    def evaluate(self, inputs, scope, mutate_scope=False):
        return inputs
    def subst(self, scope):
        return self
    def __str__(self):
        return ''
IDENTITY = Identity()

class Chain(Expression):
    def __init__(self, links):
        self.links = links
    def evaluate(self, inputs, init_scope, mutate_scope=False):
        curr = inputs
        scope = init_scope
        for i, link in enumerate(self.links):
            if isinstance(link, Link):
                if link.open_brace is Square:
                    return FloatingChain(Chain([Link(Paren, link.close_brace, link.terms)]+self.links[i+1:]), scope)
                if link.close_brace is Square and scope is init_scope and not mutate_scope:
                    scope = Scope(scope)
            curr = link.evaluate(curr, scope, mutate_scope=True)
        return curr
    def __str__(self):
        return ''.join(map(str, self.links))
    def subst(self, init_scope):
        scope = init_scope
        new_links = []
        for link in self.links:
            new_links.append(link.subst(scope))
            if isinstance(link, Link) and link.close_brace is Square:
                scope = Shadow(scope, set(term.out_key for term in link.terms))
        return Chain(new_links)

class Brace:
    @classmethod
    def unpack(cls, terms, inputs, scope):
        raise NotImplementedError()
    @classmethod
    def pack(cls, indices, inputs, outputs, scope):
        raise NotImplementedError()
    @classmethod
    def get_open_char(self):
        raise NotImplementedError()
    @classmethod
    def get_close_char(self):
        raise NotImplementedError()

class Paren(Brace):
    @classmethod
    def unpack(cls, terms, inputs, scope):
        for t in terms:
            yield t, inputs
    @classmethod
    def pack(cls, indices, inputs, outputs, scope):
        last = HNONE
        for output in outputs:
            last = output
        return last
    @classmethod
    def get_open_char(self):
        return '('
    @classmethod
    def get_close_char(self):
        return ')'

class Curly(Brace):
    @classmethod
    def unpack(cls, terms, inputs, scope):
        for t in terms:
            component = inputs.get_component(t.in_key)
            if component != HNONE:
                yield t, component
    @classmethod
    def pack(cls, indices, inputs, outputs, scope):
        return Struct({i: o for i, o in zip(indices, outputs)})
    @classmethod
    def get_open_char(self):
        return '{'
    @classmethod
    def get_close_char(self):
        return '}'

class Square(Brace):
    @classmethod
    def pack(cls, indices, inputs, outputs, scope):
        for i, o in zip(indices, outputs):
            scope[i] = o
        return HNONE
    @classmethod
    def get_open_char(self):
        return '['
    @classmethod
    def get_close_char(self):
        return ']'

class Angle(Brace):
    @classmethod
    def unpack(cls, terms, inputs, scope):
        for t in terms:
            adjunct = inputs.get_adjunct(t.in_key)
            if adjunct != HNONE:
                yield t, adjunct
    @classmethod
    def pack(cls, indices, inputs, outputs, scope):
        d = {i: o for i, o in zip(indices, outputs)}
        if len(d) == 0:
            return inputs
        return inputs.adjoin(d)
    @classmethod
    def get_open_char(self):
        return '<'
    @classmethod
    def get_close_char(self):
        return '>'

class Link(Expression):
    def __init__(self, open_brace, close_brace, terms):
        self.open_brace = open_brace
        self.close_brace = close_brace
        self.terms = terms
    def evaluate(self, inputs, scope, mutate_scope=False):
        if self.open_brace is Square:
            return FloatingChain(Chain([Link(Paren, self.close_brace, self.terms)]), scope)
        unpacked = list(self.open_brace.unpack(self.terms, inputs, scope))
        return self.close_brace.pack(
            (term.out_key for term, _ in unpacked), inputs,
            (term.evaluate(term_input, scope) for term, term_input in unpacked),
            scope if mutate_scope or self.close_brace is not Square else Protect(scope)
        )
    def __str__(self):
        return '%s%s%s' % (
            self.open_brace.get_open_char(),
            ', '.join(map(str, self.terms)),
            self.close_brace.get_close_char()
        )
    def subst(self, scope):
        return Link(self.open_brace, self.close_brace, [term.subst(scope) for term in self.terms])

class IndexedTerm(Expression):
    def __init__(self, in_key, out_key, value_expr):
        self.in_key = in_key
        self.out_key = out_key
        self.value_expr = value_expr
    def evaluate(self, inputs, scope, mutate_scope=False):
        return self.value_expr.evaluate(inputs, scope, mutate_scope)
    def __str__(self):
        if isinstance(self.in_key, int):
            if isinstance(self.out_key, int):
                return str(self.value_expr)
            return ':%s:%s' % (str(self.value_expr), str(self.out_key))
        if isinstance(self.out_key, int):
            return '%s:%s' % (str(self.in_key), str(self.value_expr))
        return '%s:%s:%s' % (str(self.in_key), str(self.value_expr), str(self.out_key))
    def subst(self, scope):
        return IndexedTerm(self.in_key, self.out_key, self.value_expr.subst(scope))

class Constant(Expression):
    def __init__(self, value):
        self.value = value
    def evaluate(self, inputs, scope, mutate_scope=False):
        return self.value
    def __str__(self):
        return str(self.value)
    def subst(self, scope):
        return self

class Reference(Expression):
    def __init__(self, key):
        self.key = key
    def evaluate(self, inputs, scope, mutate_scope=False):
        deref = scope.get(self.key, HNONE)
        if isinstance(deref, FloatingChain):
            return deref.chain.evaluate(inputs, scope)
        return deref
    def __str__(self):
        return str(self.key)
    def subst(self, scope):
        replacement = scope.get(self.key)
        if replacement:
            return Constant(replacement)
        else:
            return self
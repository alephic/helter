
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
        return '(%s}' % ', '.join('%s: %s' % (key, str(val)) for key, val in self.data.items())

class FloatingChain(Value):
    def __init__(self, chain, saved_scope, adjuncts=None):
        super().__init__(adjuncts)
        self.chain = chain
        self.saved_scope = saved_scope
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
                if link.close_brace is Square and scope is init_scope:
                    scope = Scope(scope)
            curr, scope = link.evaluate(curr, scope, mutate_scope=True)
        return curr
    def __str__(self):
        return ''.join(map(str, self.links))

class Brace:
    @classmethod
    def unpack(cls, indices, terms, inputs, scope):
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
    def unpack(cls, indices, terms, inputs, scope):
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
    def unpack(cls, indices, terms, inputs, scope):
        for t, i in zip(terms, indices):
            component = inputs.get_component(i)
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
    def unpack(cls, indices, terms, inputs, scope):
        for t, i in zip(terms, indices):
            adjunct = inputs.get_adjunct(i)
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
        indices = (term.key if isinstance(term, IndexedTerm) else i for i, term in enumerate(self.terms))
        return self.close_brace.pack(
            indices, inputs,
            (term.evaluate(term_input, scope) for term, term_input in self.open_brace.unpack(indices, self.terms, inputs, scope)),
            scope if mutate_scope or self.close_brace is not Square else Protect(scope)
        )
    def __str__(self):
        return '%s%s%s' % (
            self.open_brace.get_open_char(),
            ', '.join(map(str, self.terms)),
            self.close_brace.get_close_char()
        )

class IndexedTerm(Expression):
    def __init__(self, key, value_expr):
        self.key = key
        self.value_expr = value_expr
    def evaluate(self, inputs, scope, mutate_scope=False):
        return self.value_expr.evaluate(inputs, scope, mutate_scope)
    def __str__(self):
        return '%s: %s' % (str(self.key), str(self.value_expr))

class Constant(Expression):
    def __init__(self, value):
        self.value = value
    def evaluate(self, inputs, scope, mutate_scope=False):
        return self.value
    def __str__(self):
        return repr(self.value)

class Reference(Expression):
    def __init__(self, key):
        self.key = key
    def evaluate(self, inputs, scope, mutate_scope=False):
        deref = scope.get(self.key, HNONE)
        if isinstance(deref, FloatingChain):
            return deref.chain.evaluate(inputs, deref.saved_scope)
        return deref
    def __str__(self):
        return str(self.key)
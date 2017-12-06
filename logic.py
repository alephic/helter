
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
        s = Value()
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

class HelterNone(Value):
    def __init__(self):
        pass
    def get_adjunct(self, index):
        return self
    def get_component(self, index):
        return self
    def adjoin(self, d):
        return Value(d)

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
    def __repr__(self):
        if len(self.adjuncts) == 0:
            return 'Struct(%s)' % repr(self.data)
        else:
            return 'Struct(%s, adjuncts=%s)' % (repr(self.data), repr(self.adjuncts))

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
    def __repr__(self):
        if len(self.adjuncts) == 0:
            return 'FloatingChain(%s)' % str(self.chain)
        else:
            return 'FloatingChain(%s, adjuncts=%s)' % (str(self.chain), repr(self.adjuncts))

class Expression:
    def evaluate(self, inputs, scope):
        raise NotImplementedError()

class Chain(Expression):
    def __init__(self, links):
        self.links = links
    def evaluate(self, inputs, scope):
        curr = inputs
        for i, link in enumerate(self.links):
            if link.open_brace is Square:
                modified = Link(Curly, link.close_brace, link.terms)
                return FloatingChain(Chain([modified]+self.links[i+1:]), scope)
            prev = curr
            curr = link.evaluate(prev, scope)
            if isinstance(curr, FloatingChain):
                curr = curr.chain.evaluate(prev, curr.saved_scope)
        return curr
    def __str__(self):
        return ''.join(map(str, self.links))

class Brace:
    @classmethod
    def unpack(cls, indices, inputs, scope):
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
    def unpack(cls, indices, inputs, scope):
        for _ in indices:
            yield inputs
    @classmethod
    def pack(cls, indices, inputs, outputs, scope):
        last = None
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
    def unpack(cls, indices, inputs, scope):
        for i in indices:
            yield inputs.get_component(i)
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
    def unpack(cls, indices, inputs, scope):
        for i in indices:
            yield inputs.get_adjunct(i)
    @classmethod
    def pack(cls, indices, inputs, outputs, scope):
        d = {i: o for i, o in zip(indices, outputs)}
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
    def evaluate(self, inputs, scope):
        indices = [term.key if isinstance(term, IndexedTerm) else i for i, term in enumerate(self.terms)]
        return self.close_brace.pack(
            indices, inputs,
            (term.evaluate(term_input, Scope(scope)) for term, term_input in zip(self.terms, self.open_brace.unpack(indices, inputs, scope))),
            scope
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
    def evaluate(self, inputs, scope):
        return self.value_expr.evaluate(inputs, scope)
    def __str__(self):
        return '%s: %s' % (str(self.key), str(self.value_expr))

class Constant(Expression):
    def __init__(self, value):
        self.value = value
    def evaluate(self, inputs, scope):
        return self.value
    def __str__(self):
        return repr(self.value)

class Reference(Expression):
    def __init__(self, key):
        self.key = key
    def evaluate(self, inputs, scope):
        return scope.get(self.key, HNONE)
    def __str__(self):
        return str(self.key)
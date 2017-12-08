
import logic
import operator
import parse

BUILTINS = {}

class WrappedFunc(logic.Expression):
    def __init__(self, f):
        self.f = f
    def evaluate(self, inputs, scope):
        return self.f(inputs)
    def subst(self, scope):
        return self
    def __repr__(self):
        return '?BUILTIN FUNCTION?'

def type_check(val, type_name):
    return val.get_adjunct('type').get_component('which').get_component(type_name) is not logic.HNONE

def arg_struct_type_check(x, *pos):
    return all(type_check(x.get_component(i), t) for i, t in enumerate(pos))

def unary_op(op_func, result_boxer, t):
    def f(x):
        if type_check(x, t):
            return result_boxer(op_func(x.content))
        return logic.HNONE
    return logic.FloatingChain(WrappedFunc(f))

def binary_op(op_func, result_boxer, t1, t2):
    def f(x):
        if arg_struct_type_check(x, t1, t2):
            return result_boxer(op_func(x.data[0].content, x.data[1].content))
        return logic.HNONE
    return logic.FloatingChain(WrappedFunc(f))

def unary_op_dispatch(op_id):
    return logic.FloatingChain(logic.Chain([
        logic.Link(logic.Paren, logic.Square, [logic.IndexedTerm(0,'x',logic.IDENTITY)]),
        logic.Reference('x'),
        logic.Link(logic.Angle, logic.Paren, [
            logic.IndexedTerm('type', 0, logic.Chain([
                logic.Link(logic.Curly, logic.Square, [
                    logic.IndexedTerm(op_id, 'op', logic.IDENTITY)]
                ),
                logic.Reference('x'),
                logic.Reference('op')
            ]))
        ])
    ]))

def binary_op_dispatch(op_id):
    return logic.FloatingChain(logic.Chain([
        logic.Link(logic.Curly, logic.Square, [
            logic.IndexedTerm(0,'x',logic.IDENTITY),
            logic.IndexedTerm(1,'y',logic.IDENTITY)
        ]),
        logic.Reference('x'),
        logic.Link(logic.Angle, logic.Paren, [
            logic.IndexedTerm('type', 0, logic.Chain([
                logic.Link(logic.Curly, logic.Square, [
                    logic.IndexedTerm(op_id, 'op', logic.IDENTITY)]
                ),
                logic.Link(logic.Paren, logic.Curly, [
                    logic.IndexedTerm(0, 0, logic.Reference('x')),
                    logic.IndexedTerm(1, 1, logic.Reference('y'))
                ]),
                logic.Reference('op')
            ]))
        ])
    ]))

UNIT_TYPE = logic.Struct({})
HUNIT = logic.Symbol(name='unit', adjuncts={'type': UNIT_TYPE})
UNIT_TYPE.data['which'] = logic.Struct({'unit_type': HUNIT})
BUILTINS['unit'] = HUNIT

BOOL_TYPE = logic.Struct({})
BOOL_TYPE.data['which'] = logic.Struct({'bool': HUNIT})
HTRUE = logic.Struct({}, adjuncts={'type': BOOL_TYPE})
HTRUE.data['true'] = HUNIT
BUILTINS['true'] = HTRUE
HFALSE = logic.Struct({}, adjuncts={'type': BOOL_TYPE})
HFALSE.data['false'] = HUNIT
BUILTINS['false'] = HFALSE

def bool_box(x):
    return HTRUE if x else HFALSE

def bool_not(x):
    if x is HFALSE:
        return HTRUE
    if x is HTRUE:
        return HFALSE
    return logic.HNONE
BOOL_TYPE.data['!'] = logic.FloatingChain(WrappedFunc(bool_not), {})

def bool_and(x):
    if arg_struct_type_check(x, 'bool', 'bool'):
        return bool_box(x.data[0] == HTRUE and x.data[1] == HTRUE)
    return logic.HNONE
BOOL_TYPE.data['&'] = logic.FloatingChain(WrappedFunc(bool_and), {})

def bool_or(x):
    if arg_struct_type_check(x, 'bool', 'bool'):
        return bool_box(x.data[0] == HTRUE or x.data[1] == HTRUE)
    return logic.HNONE
BOOL_TYPE.data['|'] = logic.FloatingChain(WrappedFunc(bool_or), {})

def bool_eq(x):
    if arg_struct_type_check(x, 'bool', 'bool'):
        return bool_box(x.data[0] == x.data[1])
    return logic.HNONE
BOOL_TYPE.data['='] = logic.FloatingChain(WrappedFunc(bool_eq), {})

INT_TYPE = logic.Struct({})
INT_TYPE.data['which'] = logic.Struct({'int': HUNIT})
def int_box(x):
    return logic.Boxed(x, adjuncts={'type': INT_TYPE})
INT_TYPE.data['+'] = binary_op(operator.add, int_box, 'int', 'int')
INT_TYPE.data['-'] = binary_op(operator.sub, int_box, 'int', 'int')
INT_TYPE.data['*'] = binary_op(operator.mul, int_box, 'int', 'int')
INT_TYPE.data['/'] = binary_op(operator.floordiv, int_box, 'int', 'int')
INT_TYPE.data['%'] = binary_op(operator.mod, int_box, 'int', 'int')
INT_TYPE.data['='] = binary_op(operator.eq, int_box, 'int', 'int')
INT_TYPE.data['>'] = binary_op(operator.gt, bool_box, 'int', 'int')
INT_TYPE.data['<'] = binary_op(operator.lt, bool_box, 'int', 'int')
INT_TYPE.data['>='] = binary_op(operator.ge, bool_box, 'int', 'int')
INT_TYPE.data['<='] = binary_op(operator.le, bool_box, 'int', 'int')

FLOAT_TYPE = logic.Struct({})
FLOAT_TYPE.data['which'] = logic.Struct({'float': HUNIT})
def float_box(x):
    return logic.Boxed(x, adjuncts={'type': FLOAT_TYPE})
FLOAT_TYPE.data['+'] = binary_op(operator.add, float_box, 'float', 'float')
FLOAT_TYPE.data['-'] = binary_op(operator.sub, float_box, 'float', 'float')
FLOAT_TYPE.data['*'] = binary_op(operator.mul, float_box, 'float', 'float')
FLOAT_TYPE.data['/'] = binary_op(operator.floordiv, float_box, 'float', 'float')
FLOAT_TYPE.data['%'] = binary_op(operator.mod, float_box, 'float', 'float')
FLOAT_TYPE.data['>'] = binary_op(operator.gt, bool_box, 'float', 'float')
FLOAT_TYPE.data['<'] = binary_op(operator.lt, bool_box, 'float', 'float')

STRING_TYPE = logic.Struct({})
STRING_TYPE.data['which'] = logic.Struct({'string': HUNIT})
def string_box(s):
    return logic.Boxed(s, adjuncts={'type': STRING_TYPE})
STRING_TYPE.data['+'] = binary_op(operator.concat, string_box, 'string', 'string')
STRING_TYPE.data['length'] = unary_op(len, int_box, 'string')
STRING_TYPE.data['='] = binary_op(operator.eq, bool_box, 'string', 'string')

for op in ['!', 'length']:
    BUILTINS[op] = unary_op_dispatch(op)
for op in ['&', '|', '+', '-', '*', '/', '%', '<', '>', '<=', '>=', '=']:
    BUILTINS[op] = binary_op_dispatch(op)
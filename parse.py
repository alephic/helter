import re
from logic import *
import helter_builtins

OPEN = re.compile(r'[\(\[\{<]')
CLOSE = re.compile(r'[\)\]\}>]')
COMMA = re.compile(r',')
COLON = re.compile(r':')
QUOTE = re.compile(r'"')
ESCAPE = re.compile(r'\\(["\\abrntfv]|x[a-fA-F0-9]{2}|u[a-fA-F0-9]{4}|U[a-fA-F0-9]{8})')
INT = re.compile(r'-?[0-9]+')
FLOAT = re.compile(r'-?([0-9]*\.[0-9]+|[0-9]+\.[0-9]*)')
SYM = re.compile(r'[^()\[\]\s\{\}<>,:"]+')
SPACES = re.compile(r'(\s|#[^\n]*)*')

class Tracker:
  def __init__(self, s, pos=0):
    self.s = s
    self.pos = pos

def parse_re(r, t):
    m = r.match(t.s, pos=t.pos)
    if m:
        t.pos = m.end()
        return m.group(0)
    return None

UNIQUE = {}

def parse_reference(t):
    s = parse_re(SYM, t)
    if s:
        return Reference(s)
    return None

ESCAPE_CHARS = {'"':'"', '\\':'\\', 'a':'\a', 'b':'\b', 'r':'\r', 'n':'\n', 't':'\t', 'f':'\f', 'v':'\v'}

def parse_string(t):
    reset = t.pos
    s = parse_re(QUOTE, t)
    if s:
        chars = []
        while True:
            e = parse_re(ESCAPE, t)
            if e:
                if e[1] in 'xuU':
                    chars += chr(int(e[2:], base=16))
                else:
                    chars += ESCAPE_CHARS.get(e[1], e[1])
            elif parse_re(QUOTE, t):
                return Constant(helter_builtins.string_box(''.join(chars)))
            else:
                chars.append(t.s[t.pos])
                t.pos += 1
    t.pos = reset
    return None

def parse_num(t):
    n = parse_re(FLOAT, t)
    if n:
        return Constant(helter_builtins.float_box(float(n)))
    n = parse_re(INT, t)
    if n:
        return Constant(helter_builtins.int_box(int(n)))
    return None

def parse_open(t):
    m = parse_re(OPEN, t)
    if m:
        return {'(': Paren, '{': Curly, '[': Square, '<': Angle}[m]
    return None

def parse_close(t):
    m = parse_re(CLOSE, t)
    if m:
        return {')': Paren, '}': Curly, ']': Square, '>': Angle}[m]
    return None

def parse_link(t):
    reset = t.pos
    o = parse_open(t)
    if o:
        terms = []
        while True:
            parse_re(SPACES, t)
            term = parse_term(t, len(terms))
            if term:
                terms.append(term)
            parse_re(SPACES, t)
            c = parse_close(t)
            if c:
                return Link(o, c, terms)
            if not parse_re(COMMA, t):
                break
    t.pos = reset
    return None

def parse_term(t, i):
    reset = t.pos
    i_k = parse_re(SYM, t)
    parse_re(SPACES, t)
    if parse_re(COLON, t):
        parse_re(SPACES, t)
        e = parse_expr(t)
        parse_re(SPACES, t)
        o_k = None
        if parse_re(COLON, t):
            parse_re(SPACES, t)
            o_k = parse_re(SYM, t)
        return IndexedTerm(i_k or i, o_k or i, e or IDENTITY)
    t.pos = reset
    e = parse_expr(t)
    if e:
        return IndexedTerm(i, i, e)
    t.pos = reset
    return None

def parse_expr_not_chain(t):
    return parse_num(t) or parse_string(t) or parse_reference(t) or parse_link(t)

def parse_expr(t):
    reset = t.pos
    e = parse_expr_not_chain(t)
    if e:
        chain = [e]
        while True:
            parse_re(SPACES, t)
            link = parse_expr_not_chain(t)
            if link:
                chain.append(link)
            else:
                if len(chain) == 1:
                    return chain[0]
                else:
                    return Chain(chain)
    t.pos = reset
    return None

def parse(s):
    return parse_expr(Tracker(s))
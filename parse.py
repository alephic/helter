import re
from logic import *

OPEN = re.compile(r'[\(\[\{<]')
CLOSE = re.compile(r'[\)\]\}>]')
COMMA = re.compile(r',')
COLON = re.compile(r':')
SYM = re.compile(r'[^()\[\]\s\{\}<>,:]+')
SPACES = re.compile(r'\s*')

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

def parse_open(t):
    m = parse_re(OPEN, t)
    if m:
        return {'(': PAREN, '{': CURLY, '[': SQUARE, '<': ANGLE}[m]
    return None

def parse_close(t):
    m = parse_re(CLOSE, t)
    if m:
        return {')': PAREN, '}': CURLY, ']': SQUARE, '>': ANGLE}[m]
    return None

def parse_link(t):
    reset = t.pos
    o = parse_open(t)
    if o:
        terms = []
        while True:
            parse_re(SPACES, t)
            term = parse_term(t)
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

def parse_term(t):
    reset = t.pos
    e = parse_expr(t)
    if e:
        parse_re(SPACES, t)
        if isinstance(e, Reference) and parse_re(COLON, t):
            parse_re(SPACES, t)
            v = parse_expr(t)
            if v:
                return IndexedTerm(e.key, v)
        else:
            return e
    t.pos = reset
    return None

def parse_expr_not_chain(t):
    return parse_reference(t) or parse_link(t)

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

try:
    import readline
except ImportError as e:
    pass
import parse
import logic
import sys

def repl(init_value=None, scope=None):
    curr = init_value or logic.HNONE
    scope = scope or logic.Scope(logic.SymbolPool())
    while True:
        i = input('> ')
        if i == ':q':
            quit()
        if len(i) == 0:
            continue
        p = parse.parse(i)
        if p:
            try:
                new_val = p.evaluate(curr, scope)
            except Exception as e:
                print(e)
                continue
            print(new_val)
            curr = new_val
        else:
            print('Invalid syntax', sys.stderr)

if __name__ == "__main__":
    repl()
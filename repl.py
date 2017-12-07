try:
    import readline
except ImportError as e:
    pass
import parse
import logic
import helter_builtins
import sys

def repl(init_value=None, scope=None):
    curr = init_value or logic.HNONE
    scope = scope or logic.Scope(helter_builtins.BUILTINS)
    while True:
        i = input('> ')
        if i == ':q':
            quit()
        if len(i) == 0:
            continue
        p = parse.parse(i)
        if p:
            new_val = p.evaluate(curr, scope, mutate_scope=True)
            print(new_val)
            curr = new_val
        else:
            print('Invalid syntax', sys.stderr)

if __name__ == "__main__":
    repl()
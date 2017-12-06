import logic
import parse
import sys

if __name__ == "__main__":
  if len(sys.argv) == 1:
    import repl
    repl.repl()
  else:
    with open(sys.argv[1]) as f:
      p = parse.parse(f.read())
      if p:
        p.evaluate(logic.HNONE, logic.Scope(logic.SymbolPool()))
      else:
        print('Invalid syntax', file=sys.stderr)

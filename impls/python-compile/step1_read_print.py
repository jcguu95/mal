import traceback, mal_readline, reader

_lisp_prompt = "user> "

def READ(str):
    return reader.read(str)

def EVAL(ast, env):
    return ast

def PRINT(exp):
    return exp

def REP(str):
    return PRINT(EVAL(READ(str), None))

def REPL():
    while True:
        try:
            line = mal_readline.input_(_lisp_prompt)
            print(REP(line))
        except EOFError:
            break
        except Exception as exc:
            traceback.print_exception(exc, limit=10)

LISP = REPL

if __name__ == "__main__":
    LISP()

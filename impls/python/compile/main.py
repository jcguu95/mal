import sys, traceback, code
import mal_readline
import mal_types as types
import reader, printer
from env import Env
import core

# debug
from loguru import logger
logger.info("Debugger Activated: loguru")
_line_history, _ast_history = [], []
sys.ps1, sys.ps2 = "[PYTHON]> ", "        > "
_wake_up_command = ";()"

# read
def READ(str):
    return reader.read_str(str)

def compile_symbol (ast, env, prefix):
    logger.debug(f"Compiling AST:\n{ast}\n")
    compiled_strings = \
[f"""
# compile_symbol
def {prefix} (ast, env):
    logger.debug(f"ast: {{ast}}")
    result = env.get(ast)
    logger.debug(f"result: {{result}}")
    return result
"""]
    return compiled_strings

def compile_def (ast, env, prefix):
    logger.debug(f"Compiling AST:\n{ast}\n")
    compiled_strings = \
[f"""
# compile_def
def {prefix} (ast, env):
    logger.debug(f"ast: {{ast}}")
    result = env.set(ast[1], {prefix}_0(ast[2], env))
    logger.debug(f"result: {{result}}")
    return result
"""]
    compiled_strings = COMPILE(ast[2], env, prefix=f"{prefix}_0")[0] + compiled_strings
    return compiled_strings

def compile_let (ast, env, prefix):
    logger.debug(f"Compiling AST:\n{ast}\n")
    compiled_strings = []
    for i in range(1, len(ast[1]), 2):
        compiled_strings += COMPILE(ast[1][i], env, prefix=f"{prefix}_{(i-1)//2}")[0]
    compiled_strings += COMPILE(ast[2], env, prefix=f"{prefix}_{(i+1)//2}")[0]
    compiled_string = \
f"""
# compile_let
def {prefix} (ast, env):
    logger.debug(f"ast: {{ast}}")
    let_env = Env(env)"""
    for i in range(0, len(ast[1]), 2):
        compiled_string += \
f"""
    let_env.set(ast[1][{i}], {prefix}_{i//2}(ast[1][{i+1}], let_env))"""
    compiled_string += \
f"""
    result = {prefix}_{(i+2)//2}(ast[2], let_env)
    logger.debug(f"result: {{result}}")
    return result
"""
    compiled_strings += [compiled_string]
    return compiled_strings

def compile_do (ast, env, prefix):
    logger.debug(f"Compiling AST:\n{ast}\n")
    compiled_string = \
f"""
# compile_do
def {prefix} (ast, env):
    logger.debug(f"ast: {{ast}}")
"""
    for i in range(1, len(ast)-1):
        compiled_string += \
f"""
    {prefix}_{i-1}(ast[{i}], env)
"""
    i += 1
    compiled_string += \
f"""
    result = {prefix}_{i-1}(ast[{i}], env)
    logger.debug(f"result: {{result}}")
    return result
"""
    compiled_strings = []
    for i in range(1, len(ast)):
        compiled_strings += COMPILE(ast[i], env, prefix=f"{prefix}_{i-1}")[0]
    compiled_strings += [compiled_string]
    return compiled_strings

def compile_if (ast, env, prefix):
    logger.debug(f"Compiling AST:\n{ast}\n")
    compiled_string = \
f"""
# compile_if
def {prefix} (ast, env):
    logger.debug(f"ast: {{ast}}")
    cond = {prefix}_0(ast[1], env)
    if not (cond is None or cond is False):
        result = {prefix}_1 (ast[2], env)
    else:
        result = {prefix}_2 (ast[3], env)
    logger.debug(f"result: {{result}}")
    return result
"""
    cond_compiled_strings = COMPILE(ast[1], env, prefix=f"{prefix}_0")[0]
    if_compiled_strings = COMPILE(ast[2], env, prefix=f"{prefix}_1")[0]
    else_compiled_strings = COMPILE(ast[3], env, prefix=f"{prefix}_2")[0]
    compiled_strings = cond_compiled_strings + if_compiled_strings + else_compiled_strings + [compiled_string]
    return compiled_strings

def compile_funcall (ast, env, prefix):
    logger.debug(f"Compiling AST:\n{ast}\n")
    compiled_string = \
f"""
# compile_funcall
def {prefix} (ast, env):
    logger.debug(f"ast: {{ast}}")
    result = {prefix}_{0}(ast[0], env) \\
"""
    compiled_string += "   (\n"
    for i in range(1, len(ast)):
        compiled_string += f"        {prefix}_{i}(ast[{i}], env),\n"
    compiled_string += "   )"
    compiled_string += \
f"""
    logger.debug(f"result: {{result}}")
    return result
"""
    compiled_strings = [compiled_string]
    for i in range(0, len(ast)):
        compiled_strings = COMPILE(ast[i], env, prefix=f"{prefix}_{i}")[0] + compiled_strings
    return compiled_strings

def compile_identity (ast, env, prefix):
    logger.debug(f"Compiling AST:\n{ast}\n")
    compiled_strings = \
[f"""
# compile_identity
def {prefix} (ast, env):
    logger.debug(f"ast: {{ast}}")
    result = ast
    logger.debug(f"result: {{result}}")
    return result
"""]
    return compiled_strings

def compile_scalar (ast, env, prefix):
    logger.debug(f"Compiling AST:\n{ast}\n")
    if types._string_Q(ast): ast = f"\"{ast}\""
    compiled_strings = \
[f"""
# compile_scalar
def {prefix} (ast, env):
    logger.debug(f"ast: {{ast}}")
    result = {ast}
    logger.debug(f"result: {{result}}")
    return result
"""]
    return compiled_strings

def compile_fn (ast, env, prefix):
    logger.debug(f"Compiling AST:\n{ast}\n")
    compiled_string = \
f"""
# compile_fn
def {prefix} (ast, env):
    # logger.debug(f"ast: {{ast}}")
    def {prefix}_lambda (*args):
        # logger.debug(f"args: {{args}}")
        params = ast[1]
        # logger.debug(f"ast: {{ast}}")
        # logger.debug(f"params: {{params}}")
        local_env = Env(env, params, types.List(args))
        return {prefix}_0(ast[2], local_env)
    result = {prefix}_lambda
    # logger.debug(f"result: {{result}}")
    return result
"""
    compiled_strings = COMPILE(ast[2], env, prefix=f"{prefix}_0")[0] + [compiled_string]
    return compiled_strings

def compile_quote (ast, env, prefix):
    logger.debug(f"Compiling AST:\n{ast}\n")
    compiled_strings = \
[f"""
def {prefix} (ast, env):
    logger.debug(f"ast: {{ast}}")
    result = ast[1]
    logger.debug(f"result: {{result}}")
    return result
"""]
    return compiled_strings

def is_macro_call (ast, env):
    return (types._list_Q(ast) and
            types._symbol_Q(ast[0]) and
            env.find(ast[0]) and
            hasattr(env.get(ast[0]), '_ismacro_'))

def macroexpand (ast, env):
    count, unexpanded_ast = 0, ast
    while is_macro_call(ast, env):
        count += 1
        logger.debug(f"Macro Expansion\n> AST:\n{ast}\n")
        macro_fn = env.get(ast[0])
        ast = macro_fn(*ast[1:])
        logger.debug(f"Macro Expansion Finished ({count} fold(s)).\n> New AST:\n{ast}\n> Old AST:\n{unexpanded_ast}\n")
    return ast

def COMPILE (ast, env, prefix="blk"):
    logger.debug(f"Compiling AST:\n{ast}\n")
    ast = macroexpand(ast, env)
    if types._symbol_Q(ast):
        compiled_strings = compile_symbol(ast, env, prefix)
    elif types._list_Q(ast):
        if len(ast) == 0:        compiled_strings = compile_scalar(None, env, prefix)
        elif ast[0] == "def!":   compiled_strings = compile_def(ast, env, prefix)
        elif ast[0] == "let*":   compiled_strings = compile_let(ast, env, prefix)
        elif ast[0] == "do":     compiled_strings = compile_do(ast, env, prefix)
        elif ast[0] == "if":     compiled_strings = compile_if(ast, env, prefix)
        elif ast[0] == "fn*":    compiled_strings = compile_fn(ast, env, prefix)
        elif ast[0] == "quote":  compiled_strings = compile_quote(ast, env, prefix)
        else:                    compiled_strings = compile_funcall(ast, env, prefix)
    elif types._scalar_Q(ast):   compiled_strings = compile_scalar(ast, env, prefix)
    elif types._function_Q(ast): compiled_strings = compile_identity(ast, env, prefix)
    elif types._vector_Q(ast) or types._hash_map_Q(ast):
        raise Exception("Unsupported Type: Vector or Hash Map.") # TODO
    else:
        raise Exception(f"Unknown AST Type: {type(ast)}")
    return compiled_strings, ast, env

def EXEC (compiled_strings, ast, env):
    compiled_strings += ["\nRET = blk(ast, env)\n"] # This is executed later in the for loop, using the ast and env in the input.
    logger.debug(f"[BEGIN] Code to Execute\nCompiled from AST:\n{ast}\n")
    for code in compiled_strings:
        logger.debug(f"[.....] Code to Execute\n{code}")
    logger.debug(f"[ END ] Code to Execute\n")
    bindings = globals().copy()
    bindings.update(locals())
    for code in compiled_strings:
        exec(code, bindings, bindings)
    return bindings["RET"]

# eval
def EVAL(ast, env):
    logger.debug(f"EVAL AST: {ast}\n")
    _ast_history.append(ast)
    return EXEC(*COMPILE(ast, env))

# print
def PRINT(exp):
    return printer._pr_str(exp)

# environment
repl_env = Env()

# repl
def REP(str):
    return PRINT(EVAL(READ(str), repl_env))

# load from core
for k, v in core.ns.items(): repl_env.set(types._symbol(k), v)
repl_env.set(types._symbol('eval'), lambda ast: EVAL(ast, repl_env))
repl_env.set(types._symbol('*ARGV*'), types._list(*sys.argv[2:]))
repl_env.set(types._symbol('debugger'), lambda x: logger.remove() if x == 0 else logger.add(sys.stderr, level="DEBUG"))
repl_env.set(types._symbol('set-ismacro'), lambda fn: setattr(fn, '_ismacro_', True))
repl_env.set(types._symbol('unset-ismacro'), lambda fn: setattr(fn, '_ismacro_', False))
repl_env.set(types._symbol('ismacro'), lambda fn: getattr(fn, '_ismacro_', False))

logger.remove()
REP("(def! defmacro! (fn* (name function-ast) (list 'do (list 'def! name (eval function-ast)) (list 'set-ismacro name))))") # TODO Rewrite after having quasiquote.
REP("(set-ismacro defmacro!)") # This defines the macro `defmacro!`
logger.add(sys.stderr, level="DEBUG")
REP("(defmacro! cond (fn* (& xs) (if (> (count xs) 0) (list 'if (first xs) (if (> (count xs) 1) (nth xs 1) (throw \"odd number of forms to cond\")) (cons 'cond (rest (rest xs)))))))")

# automatic tests
logger.info("Running tests..")
logger.remove()
assert(EVAL(READ("nil"), repl_env) == None)
assert(EVAL(READ("true"), repl_env) == True)
assert(EVAL(READ("false"), repl_env) == False)
assert(EVAL(READ("123"), repl_env) == 123)
assert(EVAL(READ("\"This is a string.\""), repl_env) == "This is a string.")
assert(EVAL(READ("()"), repl_env) == None)
assert(EVAL(READ("(+ 1 1)"), repl_env) == 2)
assert(EVAL(READ("(+ (* 2 (+ 3 4)) 1))"), repl_env) == 15)
assert(EVAL(READ("(+)"), repl_env) == 0)
assert(EVAL(READ("(-)"), repl_env) == 0)
assert(EVAL(READ("(- 9)"), repl_env) == -9)
assert(EVAL(READ("(- 9 2)"), repl_env) == 7)
assert(EVAL(READ("(*)"), repl_env) == 1)
assert(EVAL(READ("(let* (a 3 b 4) (+ a b))"), repl_env) == 7)
assert(EVAL(READ("(let* (a 3 b 4) (+ a (let* (b 0) b)))"), repl_env) == 3)
assert(EVAL(READ("(let* (a 3 b a) b)"), repl_env) == 3)
assert(EVAL(READ("(let* (a 3 b a) (let* (a b a a) 3))"), repl_env) == 3)
assert(EVAL(READ("(do (def! x 1) (def! y 2) (+ x y))"), repl_env) == 3)
assert(EVAL(READ("(do (def! x 8) x (def! y 9) (let* (y x x y) x))"), repl_env) == 8)
assert(EVAL(READ("(if          )"), repl_env) == None)
assert(EVAL(READ("(if 0        )"), repl_env) == None)
assert(EVAL(READ("(if 0     1  )"), repl_env) == 1)
assert(EVAL(READ("(if 0     1 2)"), repl_env) == 1)
assert(EVAL(READ("(if nil   1 2)"), repl_env) == 2)
assert(EVAL(READ("(if nil   1  )"), repl_env) == None)
assert(EVAL(READ("(if false 1 2)"), repl_env) == 2)
assert(EVAL(READ("(if (if false 0 nil) 1 2)"), repl_env) == 2)
assert(EVAL(READ("(do (def! f (fn* () a)) (def! a 9) (let* (a 0) (f)))"), repl_env) == 9) # NOTE Is this desirable?
assert(EVAL(READ("((fn* (a) a) 7)"), repl_env) == 7)
assert(EVAL(READ("((fn* (a) (* (a) (a))) (fn* (a) 3))"), repl_env) == 9)
assert(EVAL(READ("((fn* (a b) (* (a b) b)) (fn* (a) (+ 2 a)) 7)"), repl_env) == 63)
assert(EVAL(READ("((let* (a 10000 b -2) (fn* (a c) (+ a b c))) 1 1)"), repl_env) == 0)
def expect_infinite_loop (lisp_code):
    try:
        EVAL(READ(lisp_code), repl_env)
    except RecursionError:
        pass
    else:
        raise Exception("Should have given an infinite loop.")
expect_infinite_loop("((fn* (a) (a a)) (fn* (a) (a a)))")
expect_infinite_loop("(let* (f (fn* (a) (a a))) (f f))")
expect_infinite_loop("(do (def! f (fn* (a) (a a))) (def! g f) (g g))")
expect_infinite_loop("(let* (f (fn* (a) (a a)) g f) (g g))")
assert(types._function_Q(EVAL(READ("(eval +)"), repl_env)))
assert(EVAL(READ("(eval (list + 1))"), repl_env) == 1)
assert(EVAL(READ("(let* (x (atom 3)) (atom? x))"), repl_env) == True)
assert(EVAL(READ("(let* (x (atom 3)) (deref x))"), repl_env) == 3)
assert(EVAL(READ("(let* (x (atom 3)) @x)"), repl_env) == 3)
assert(EVAL(READ("(let* (x (atom 3)) (do (swap! x (fn* (n) (+ 1 n))) (deref x)))"), repl_env) == 4)
assert(EVAL(READ("(let* (x (atom 3)) (do (reset! x 9) (deref x)))"), repl_env) == 9)
assert(EVAL(READ("(quote (1 2 3))"), repl_env) == [1, 2, 3])
assert(EVAL(READ("'(1 2 3)"), repl_env) == [1, 2, 3])
assert(EVAL(READ("'+"), repl_env) == "+")
assert(EVAL(READ("\"+\""), repl_env) == "+")
assert(EVAL(READ("(= '+ \"+\")"), repl_env) == False)
assert(EVAL(READ("(cond true 1 false 2 true 3)"), repl_env) == 1)
# assert(EVAL(READ("(cond false 1 false 2 true 3)"), repl_env) == 3)
# assert(EVAL(READ("(cond false 1 false 2 false 3)"), repl_env) == None)
logger.add(sys.stderr, level="DEBUG")
logger.info("All tests passed!")
# (cond true 1 nil 2 true 3)
# (cond nil 1 nil 2 true 3)
# (cond nil 1)

# lisp repl loop
def REPL():
    global _line_history
    logger.info(f"Hint: Use `{_wake_up_command}` to get into PYTHON.")
    while True:
        try:
            line = mal_readline.readline(" (LISP) > ")
            if line == None: break
            if line == "": continue
            if line == _wake_up_command:
                logger.info(f"Hint: Use `LISP()` to get into LISP.")
                break # debug
            _line_history.append(line) # debug
            print(REP(line))
        except reader.Blank: continue
        except Exception as e:
            print("".join(traceback.format_exception(*sys.exc_info())))

LISP = REPL
REPL()

# python repl loop
code.interact(local=locals())

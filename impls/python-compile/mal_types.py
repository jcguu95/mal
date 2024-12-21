# Named mal_types because 'types' is already a standard python module.

import collections
import dataclasses
import enum
import itertools
import re
import typing
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence

# Jin
import sys, copy, types as pytypes

# The selected representations ensure that the Python == equality
# matches the MAL = equality.

# pr_str is implemented here without printer.py because
# __str__ is idiomatic and gives formatted error messages soon
# (that is, without circular dependencies or evil tricks).
# So there are three ways to format a MAL object.
# str(form)
#     the default, used by pr_seq or format strings like f'{form}'
#     implemented by form.__str__(readably=True)
# form.__str__(readably=False)
#     used by some core functions via pr_seq
#     implemented by form.__str__(readably=False)
# repr(form)
#     the python representation for debugging

class Nil(enum.Enum):
    NIL = None

    def __str__(self, readably: bool = True) -> str:
        return 'nil'


class Boolean(enum.Enum):
    FALSE = False
    TRUE = True

    def __str__(self, readably: bool = True) -> str:
        return 'true' if self is self.TRUE else 'false'


class Number(int):

    def __str__(self, readably: bool = True) -> str:
        return super().__str__()

# Scalars
def _nil_Q(exp):    return exp is None
def _true_Q(exp):   return exp is True
def _false_Q(exp):  return exp is False
def _string_Q(exp):
    if type(exp) in [String]:
        return len(exp.val)
    elif type(exp) in str_types:
        return len(exp) == 0 or exp[0] != _u("\u029e")
    else:
        return False
def _number_Q(exp): return type(exp) == int
def _scalar_Q(exp): return _nil_Q(exp) or _true_Q(exp) or _false_Q(exp) or _string_Q(exp) or _number_Q(exp)

class Symbol(str):

    def __str__(self, readably: bool = True) -> str:
        # pylint: disable=invalid-str-returned
        return self
# Jin
def _symbol_Q(exp):
    return (type(exp) == Symbol) or _string_Q(exp)

# The two other string types are wrapped in dataclasses in order to
# avoid problems with == (symbols) and pattern matching (list and
# vectors).
@dataclasses.dataclass(frozen=True, slots=True)
class String:
    val: str

    @staticmethod
    def _repl(match: re.Match[str]) -> str:
        char = match.group()
        return '\\' + ('n' if char == '\n' else char)

    def __str__(self, readably: bool = True) -> str:
        return '"' + re.sub(r'[\\"\n]', String._repl, self.val) + '"' \
            if readably else self.val


@dataclasses.dataclass(frozen=True, slots=True)
class Keyword:
    val: str

    def __str__(self, readably: bool = True) -> str:
        return ':' + self.val

# Jin
def _keyword_Q(exp):
    if type(exp) in [String]:
        len(exp.val)
    elif type(exp) in str_types:
        return len(exp) != 0 and exp[0] == _u("\u029e")
    else:
        return False


class List(tuple['Form', ...]):
    # Avoid a name clash with typing.List. This improves mypy output.

    def __init__(self, _: Iterable['Form'] = (),
                 meta: 'Form' = Nil.NIL) -> None:
        """Add a meta field, tuple.__new__ does the rest."""
        self.meta = meta

    def __str__(self, readably: bool = True) -> str:
        return '(' + pr_seq(self, readably) + ')'
# Jin
def _list_Q(exp):   return type(exp) == List
def _sequential_Q(seq): return _list_Q(seq) or _vector_Q(seq)


class Vector(tuple['Form', ...]):

    def __init__(self, _: Iterable['Form'] = (),
                 meta: 'Form' = Nil.NIL) -> None:
        """Add a meta field, tuple.__new__ does the rest."""
        self.meta = meta

    def __str__(self, readably: bool = True) -> str:
        return '[' + pr_seq(self, readably) + ']'
# Jin
def _vector_Q(exp): return type(exp) == Vector

class Map(dict[Keyword | String, 'Form']):

    def __init__(self,
                 arg: Iterable[tuple[Keyword | String, 'Form']]
                 | Mapping[Keyword | String, 'Form'] = (),
                 meta: 'Form' = Nil.NIL,
                 ) -> None:
        dict.__init__(self, arg)
        self.meta = meta

    def __str__(self, readably: bool = True) -> str:
        return '{' + pr_seq(itertools.chain.from_iterable(self.items()),
                            readably) + '}'

    @staticmethod
    def cast_items(args: Iterable['Form']
                   ) -> Iterator[tuple[Keyword | String, 'Form']]:
        key: Keyword | String | None = None
        for form in args:
            if key:
                yield key, form
                key = None
            elif isinstance(form, (Keyword, String)):
                key = form
            else:
                raise Error(f'{key} is not a valid map key')
        if key:
            raise Error(f'odd count in map binds, no value for {form}')

# FIXME Hash_Map (from Jin) and Map (from new code) are conflicted.
class Hash_Map(dict): pass
def _hash_map(*key_vals):
    hm = Hash_Map()
    for i in range(0,len(key_vals),2): hm[key_vals[i]] = key_vals[i+1]
    return hm
def _hash_map_Q(exp): return type(exp) == Hash_Map

Env = collections.ChainMap[str, 'Form']
PythonCall = Callable[[Sequence['Form']], 'Form']


class TCOEnv(typing.NamedTuple):
    body: 'Form'
    fenv: Callable[[Sequence['Form']], Env]


@dataclasses.dataclass(frozen=True, slots=True)
class Fn:
    call: PythonCall
    tco_env: TCOEnv | None = None
    meta: 'Form' = Nil.NIL

    def __str__(self, readably: bool = True) -> str:
        return '#<function>'


@dataclasses.dataclass(frozen=True, slots=True)
class Macro:
    call: PythonCall

    def __str__(self, readably: bool = True) -> str:
        return '#<macro>'


@dataclasses.dataclass(slots=True)
class Atom:
    val: 'Form'

    def __str__(self, readably: bool = True) -> str:
        return f'(atom {self.val})'
# Jin
def _atom_Q(exp):   return type(exp) == Atom

Form = (Atom | Boolean | Fn | Keyword | Macro | List
        | Map | Hash_Map | Nil | Number | String | Symbol | Vector)


class Error(Exception):
    """Local exceptions, as recommended by pylint."""


@dataclasses.dataclass(frozen=True, slots=True)
class ThrownException(Exception):
    form: Form


def pr_seq(args: Iterable[Form], readably: bool = True, sep: str = ' ') -> str:
    # This would be OK if the signature was usual.
    # pylint: disable-next=unnecessary-dunder-call
    return sep.join(x.__str__(readably) for x in args)

###

def _equal_Q(a, b):
    ota, otb = type(a), type(b)
    if _string_Q(a) and _string_Q(b):
        return a == b
    if not (ota == otb or (_sequential_Q(a) and _sequential_Q(b))):
        return False;
    if _symbol_Q(a):
        return a == b
    elif _list_Q(a) or _vector_Q(a):
        if len(a) != len(b): return False
        for i in range(len(a)):
            if not _equal_Q(a[i], b[i]): return False
        return True
    elif _hash_map_Q(a):
        akeys = sorted(a.keys())
        bkeys = sorted(b.keys())
        if len(akeys) != len(bkeys): return False
        for i in range(len(akeys)):
            if akeys[i] != bkeys[i]: return False
            if not _equal_Q(a[akeys[i]], b[bkeys[i]]): return False
        return True
    else:
        return a == b

def _clone(obj):
    #if type(obj) == type(lambda x:x):
    if type(obj) == pytypes.FunctionType:
        if obj.__code__:
            return pytypes.FunctionType(
                    obj.__code__, obj.__globals__, name = obj.__name__,
                    argdefs = obj.__defaults__, closure = obj.__closure__)
        else:
            return pytypes.FunctionType(
                    obj.func_code, obj.func_globals, name = obj.func_name,
                    argdefs = obj.func_defaults, closure = obj.func_closure)
    else:
        return copy.copy(obj)

# Functions
def _function(Eval, Env, ast, env, params):
    def fn(*args):
        return Eval(ast, Env(env, params, List(args))) #TODO Think - why compiling is better.
    fn.__meta__ = None
    fn.__ast__ = ast
    fn.__gen_env__ = lambda args: Env(env, params, args)
    return fn
def _function_Q(f):
    return callable(f)

def py_to_mal(obj):
        if type(obj) == list:   return List(obj)
        if type(obj) == tuple:  return List(obj)
        elif type(obj) == dict: return Hash_Map(obj)
        else:                   return obj

# python 3.0 differences
if sys.hexversion > 0x3000000:
    _u = lambda x: x
    _s2u = lambda x: x
else:
    import codecs
    _u = lambda x: codecs.unicode_escape_decode(x)[0]
    _s2u = lambda x: unicode(x)

if sys.version_info[0] >= 3:
    str_types = [str, String]
else:
    str_types = [str, unicode, String]

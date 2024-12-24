# A MAL-to-Python Compiler 

[Make a Lisp (MAL)](https://github.com/kanaka/mal/tree/master) is a Lisp
programming language designed for educational purposes, aimed at teaching
people how to implement a programming language from scratch. It currently has
multiple implementations across various programming languages, including
[`python3`](https://github.com/kanaka/mal/tree/master/impls/python3), which
interprets MAL code but does not include a compiler.

This project is a fork of an earlier version of the official `python3`
implementation, with additional enhancements to include a compiler. As a
result, it achieves performance approximately **16** times faster than the
original interpreter. It has been officially recognized and included on the
MAL project's README page. The source code for this implementation is located
in `./impls/python-compile/`.

## Examples

``` lisp
$ ./impls/python-compile/run
user> (+ 1 1)
; => 2
user> (= 0 0)
; = > true
user> (= 0 1)
; => false

user> (def! fib (fn* (N) (if (= N 0) 1 (if (= N 1) 1 (+ (fib (- N 1)) (fib (- N 2)))))))
user> fib
; => <function _blk_0.<locals>.blk_0.<locals>.blk_0_fn at 0x103cb5a80>
user> (fib 10)
; => 89
user> (let* (fib 8) (- 24 8))
; => 16

user> (defmacro! unless (fn* (pred a b) `(if ~pred ~b ~a)))
; => nil
user> (unless (= 0 1) 7 8)
; => 7
```

### Interopt with Underlying Python

``` shell
user> ;()
Python 3.12.8 (main, Dec  8 2024, 03:59:45) [Clang 14.0.0 (clang-1400.0.29.202)] on darwin
Type "help", "copyright", "credits" or "license" for more information.
(InteractiveConsole)
[PYTHON]> _lisp_prompt = 'lisp> '
[PYTHON]> LISP()
LISP()
lisp> (+ 1 1)
2
```

## ~16 Times Faster Than The Interpreted Version

Per the official performance test suite, `python-compile` is near
16 times faster than the interpreted version.

``` shell
[./mal]$ make "perf^python"
----------------------------------------------
Performance test for python:
Running: env STEP=stepA_mal MAL_IMPL=js python_MODE=python ../python/run ../tests/perf1.mal
Elapsed time: 1 msecs
Running: env STEP=stepA_mal MAL_IMPL=js python_MODE=python ../python/run ../tests/perf2.mal
Elapsed time: 4 msecs
Running: env STEP=stepA_mal MAL_IMPL=js python_MODE=python ../python/run ../tests/perf3.mal
iters over 10 seconds: 9311

[./mal]$ make "perf^python-compile"
----------------------------------------------
Performance test for python-compile:
Running: env STEP=stepA_mal MAL_IMPL=js ../python-compile/run ../tests/perf1.mal
Running: env STEP=stepA_mal MAL_IMPL=js ../python-compile/run ../tests/perf2.mal
Running: env STEP=stepA_mal MAL_IMPL=js ../python-compile/run ../tests/perf3.mal
iters over 10 seconds: 148519
```

## Passed All Substantial[^1] Official Tests

Quickly test them by running:

``` shell
[./mal]$ \
for ((i=2; i<=10; i++)); do
    [ $i -eq 10 ] && make "test^python-compile^stepA" || make "test^python-compile^step${i}"
    [ $? -ne 0 ] && { echo "Error occurred. Breaking loop."; break; }
done
```

[^1]: Passed test suites: 2, 3, 4, 5, 6, 7, 8, 9, A.

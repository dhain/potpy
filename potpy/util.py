from types import FunctionType, CodeType


def rename_args(func, argnames):
    c = func.func_code
    return FunctionType(
        CodeType(
            c.co_argcount,
            c.co_nlocals,
            c.co_stacksize,
            c.co_flags,
            c.co_code,
            c.co_consts,
            c.co_names,
            argnames,
            c.co_filename,
            c.co_name,
            c.co_firstlineno,
            c.co_lnotab,
            c.co_freevars,
            c.co_cellvars
        ),
        func.func_globals,
        func.func_name,
        func.func_defaults,
        func.func_closure
    )

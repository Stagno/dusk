from io import TextIOBase
from typing import Optional, Iterator, List
import ast
from dusk.grammar import Grammar
from dusk.errors import DuskSyntaxError

from dawn4py import compile, CodeGenBackend, set_verbosity, LogLevel
from dawn4py.serialization import pprint, make_sir, to_json as sir_to_json
from dawn4py.serialization.SIR import GridType

import os

__all__ = ["transpile", "backend_map", "default_backend"]

backend_map = {
    "ico-naive": CodeGenBackend.CXXNaiveIco,
    "ico-cuda": CodeGenBackend.CUDAIco,
}
default_backend = "ico-naive"


def iter_stencils(module: ast.Module) -> Iterator[ast.AST]:
    for stmt in module.body:
        if isinstance(stmt, ast.FunctionDef) and Grammar.is_stencil(stmt):
            yield stmt


def transpile(
    in_path: str,
    out_sir_file: Optional[TextIOBase],
    out_gencode_file: Optional[TextIOBase],
    backend: str = default_backend,
    verbose: bool = False,
) -> None:

    with open(in_path, "r") as in_file:
        in_str = in_file.read()
        in_ast = ast.parse(in_str, filename=in_path, type_comments=True)

        grammar = Grammar()

        # TODO: handle errors in different stencils separately
        stencils = [grammar.stencil(node) for node in iter_stencils(in_ast)]

        if verbose:
            set_verbosity(LogLevel.All)

        sir = make_sir(in_path, GridType.Value("Unstructured"), stencils)

        if out_sir_file is not None:
            out_sir_file.write(sir_to_json(sir))
        if out_gencode_file is not None:
            # TODO: default pass groups are bugged in Dawn, need to pass empty list of groups
            code = compile(sir, groups=[], backend=backend_map[backend])
            out_gencode_file.write(code)

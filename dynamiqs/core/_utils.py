from __future__ import annotations

import jax
import numpy as np
from jaxtyping import ArrayLike

from .._utils import obj_type_str
from ..solver import Solver
from ..time_array import TimeArray, _factory_constant
from .abstract_solver import AbstractSolver


def _astimearray(x: ArrayLike | TimeArray) -> TimeArray:
    if isinstance(x, TimeArray):
        return x
    else:
        try:
            return _factory_constant(x)
        except (TypeError, ValueError) as e:
            raise TypeError(
                f'Argument must be an array-like or a time-array object, but has type'
                f' {obj_type_str(x)}.'
            ) from e


def get_solver_class(
    solvers: dict[Solver, AbstractSolver], solver: Solver
) -> AbstractSolver:
    if not isinstance(solver, tuple(solvers.keys())):
        supported_str = ', '.join(f'`{x.__name__}`' for x in solvers)
        raise TypeError(
            f'Solver of type `{type(solver).__name__}` is not supported (supported'
            f' solver types: {supported_str}).'
        )
    return solvers[type(solver)]


def compute_vmap(
    f: callable,
    cartesian_batching: bool,
    is_batched: list[bool],
    out_axes: list[int | None],
) -> callable:
    if any(is_batched):
        if cartesian_batching:
            # iteratively map over the first axis of each batched argument
            idx_batched = np.where(is_batched)[0]
            # we apply the successive vmaps in reverse order, so that the output
            # batched dimensions are in the correct order
            for i in reversed(idx_batched):
                in_axes = [None] * len(is_batched)
                in_axes[i] = 0
                f = jax.vmap(f, in_axes=in_axes, out_axes=out_axes)
        else:
            # map over the first axis of all batched arguments
            in_axes = list(np.where(is_batched, 0, None))
            f = jax.vmap(f, in_axes=in_axes, out_axes=out_axes)

    return f

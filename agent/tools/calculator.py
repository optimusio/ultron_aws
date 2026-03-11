"""
Ultron Lightweight Agent - Calculator Tool

Evaluates safe arithmetic expressions using Python's ast module.
No external dependencies required.
"""

import ast
import logging
import operator
from typing import Any

from .base import BaseTool

logger = logging.getLogger(__name__)

_ALLOWED_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _safe_eval(node: ast.AST) -> Any:
    """Recursively evaluate an AST node using only allowed operations."""
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Unsupported constant type: {type(node.value)}")
    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _ALLOWED_OPS:
            raise ValueError(f"Unsupported operator: {op_type.__name__}")
        left = _safe_eval(node.left)
        right = _safe_eval(node.right)
        return _ALLOWED_OPS[op_type](left, right)
    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _ALLOWED_OPS:
            raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
        operand = _safe_eval(node.operand)
        return _ALLOWED_OPS[op_type](operand)
    raise ValueError(f"Unsupported AST node: {type(node).__name__}")


class CalculatorTool(BaseTool):
    """Safe arithmetic calculator that evaluates expressions without eval()."""

    name = "calculator"
    description = (
        "Evaluate arithmetic expressions (+, -, *, /, //, %, **). "
        "Example: calculator expression='2 ** 10 + 5 * 3'"
    )

    def run(self, expression: str = "", **kwargs: Any) -> str:  # type: ignore[override]
        """Evaluate the arithmetic expression and return the result.

        Args:
            expression: A string containing a mathematical expression.

        Returns:
            The computed result as a string, or an error message.
        """
        if not expression:
            return "⚠️  No expression provided. Usage: expression='2 + 2'"
        try:
            tree = ast.parse(expression.strip(), mode="eval")
            result = _safe_eval(tree)
            logger.debug("Calculator: %s = %s", expression, result)
            return str(result)
        except ZeroDivisionError:
            return "⚠️  Division by zero"
        except Exception as exc:
            logger.warning("Calculator error for %r: %s", expression, exc)
            return f"⚠️  Invalid expression: {exc}"

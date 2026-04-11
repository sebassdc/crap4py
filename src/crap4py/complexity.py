import ast

from crap4py.models import FunctionInfo

_SKIP_TYPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
_SIMPLE_DECISION_TYPES = (
    ast.If, ast.IfExp, ast.For, ast.AsyncFor, ast.While, ast.ExceptHandler,
)


def _node_decisions(child):
    """Decision points contributed by a single AST node (non-recursive)."""
    if isinstance(child, _SIMPLE_DECISION_TYPES):
        return 1
    if isinstance(child, ast.BoolOp):
        return len(child.values) - 1
    if isinstance(child, ast.comprehension):
        return len(child.ifs)
    if hasattr(ast, "match_case") and isinstance(child, ast.match_case):
        return 1
    return 0


def _count_decisions(node):
    """Recursively count decision points, skipping nested functions/classes."""
    count = 0
    for child in ast.iter_child_nodes(node):
        if isinstance(child, _SKIP_TYPES):
            continue
        count += _node_decisions(child) + _count_decisions(child)
    return count


def cyclomatic_complexity(source):
    """Compute cyclomatic complexity of a Python function definition string."""
    tree = ast.parse(source)
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return 1 + _count_decisions(node)
    return 1 + _count_decisions(tree)


def extract_functions(source):
    """Extract top-level functions and class methods from source, with CC."""
    tree = ast.parse(source)
    functions = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(FunctionInfo(
                name=node.name,
                start_line=node.lineno,
                end_line=node.end_lineno,
                complexity=1 + _count_decisions(node),
            ))
        elif isinstance(node, ast.ClassDef):
            for item in ast.iter_child_nodes(node):
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    functions.append(FunctionInfo(
                        name=f"{node.name}.{item.name}",
                        start_line=item.lineno,
                        end_line=item.end_lineno,
                        complexity=1 + _count_decisions(item),
                    ))
    return functions

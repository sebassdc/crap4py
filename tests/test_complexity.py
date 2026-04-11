import pytest
from crap4py.complexity import cyclomatic_complexity, extract_functions
from crap4py.models import FunctionInfo


# --- cyclomatic_complexity ---

class TestBaseComplexity:
    def test_empty_function(self):
        assert cyclomatic_complexity("def foo(): pass") == 1

    def test_no_branches(self):
        assert cyclomatic_complexity("def foo(x):\n    return x + 1") == 1


class TestIfStatements:
    def test_if(self):
        assert cyclomatic_complexity("def foo(x):\n    if x:\n        return 1\n    return 0") == 2

    def test_elif(self):
        src = "def foo(x):\n    if x > 0:\n        return 1\n    elif x < 0:\n        return -1\n    return 0"
        assert cyclomatic_complexity(src) == 3

    def test_ternary(self):
        assert cyclomatic_complexity("def foo(x):\n    return 1 if x else 0") == 2

    def test_nested_if(self):
        src = "def foo(x, y):\n    if x:\n        if y:\n            return 1\n        return 2\n    return 0"
        assert cyclomatic_complexity(src) == 3


class TestLoops:
    def test_for_loop(self):
        assert cyclomatic_complexity("def foo(xs):\n    for x in xs:\n        pass") == 2

    def test_while_loop(self):
        assert cyclomatic_complexity("def foo(x):\n    while x > 0:\n        x -= 1") == 2

    def test_async_for(self):
        src = "async def foo(xs):\n    async for x in xs:\n        pass"
        assert cyclomatic_complexity(src) == 2


class TestExceptions:
    def test_single_except(self):
        src = "def foo():\n    try:\n        bar()\n    except Exception:\n        pass"
        assert cyclomatic_complexity(src) == 2

    def test_multiple_except(self):
        src = (
            "def foo():\n"
            "    try:\n"
            "        bar()\n"
            "    except ValueError:\n"
            "        pass\n"
            "    except TypeError:\n"
            "        pass"
        )
        assert cyclomatic_complexity(src) == 3


class TestBoolOps:
    def test_and_two_values(self):
        assert cyclomatic_complexity("def foo(x, y):\n    return x and y") == 2

    def test_or_two_values(self):
        assert cyclomatic_complexity("def foo(x, y):\n    return x or y") == 2

    def test_and_three_values(self):
        assert cyclomatic_complexity("def foo(x, y, z):\n    return x and y and z") == 3

    def test_nested_bool_ops(self):
        # (a or b) and (c or d) -> 3 decisions total
        src = "def foo(a, b, c, d):\n    return (a or b) and (c or d)"
        assert cyclomatic_complexity(src) == 4  # outer and(1) + left or(1) + right or(1) = 3 → base 1+3=4


class TestComprehensions:
    def test_list_comp_with_condition(self):
        assert cyclomatic_complexity("def foo(xs):\n    return [x for x in xs if x > 0]") == 2

    def test_list_comp_two_conditions(self):
        src = "def foo(xs):\n    return [x for x in xs if x > 0 if x < 10]"
        assert cyclomatic_complexity(src) == 3

    def test_list_comp_no_condition(self):
        assert cyclomatic_complexity("def foo(xs):\n    return [x for x in xs]") == 1


class TestNestedFunctions:
    def test_nested_function_skipped(self):
        src = (
            "def foo(x):\n"
            "    def inner(y):\n"
            "        if y:\n"
            "            return 1\n"
            "    return inner(x)"
        )
        assert cyclomatic_complexity(src) == 1

    def test_nested_class_skipped(self):
        src = (
            "def foo(x):\n"
            "    class Inner:\n"
            "        def method(self):\n"
            "            if x:\n"
            "                return 1\n"
            "    return Inner()"
        )
        assert cyclomatic_complexity(src) == 1


class TestMatchCase:
    def test_match_case_counts_each_case(self):
        src = (
            "def foo(x):\n"
            "    match x:\n"
            "        case 1:\n"
            "            return 'one'\n"
            "        case 2:\n"
            "            return 'two'\n"
            "        case _:\n"
            "            return 'other'"
        )
        # 3 cases -> 3 decisions -> CC 4
        assert cyclomatic_complexity(src) == 4


class TestModuleLevel:
    def test_module_level_source_with_branches(self):
        # cyclomatic_complexity falls back to module-level counting
        # when source has no function definition.
        src = "if x:\n    y = 1\nelse:\n    y = 0"
        assert cyclomatic_complexity(src) == 2


class TestCombined:
    def test_multiple_decision_points(self):
        src = (
            "def foo(x, y):\n"
            "    if x:\n"
            "        if y:\n"
            "            return 1\n"
            "    elif x and y:\n"
            "        return 2\n"
            "    return 0"
        )
        # outer_if(1) + inner_if(1) + elif_if(1) + and(1) = 4 decisions -> CC 5
        assert cyclomatic_complexity(src) == 5


# --- extract_functions ---

class TestExtractFunctions:
    def test_basic_extraction(self):
        source = "def bar(x):\n    if x:\n        return 1\n    return 0\n\ndef baz(y):\n    return y"
        fns = extract_functions(source)
        assert len(fns) == 2
        assert isinstance(fns[0], FunctionInfo)
        assert fns[0].name == "bar"
        assert fns[0].start_line == 1
        assert fns[0].end_line == 4
        assert fns[1].name == "baz"
        assert fns[1].start_line == 6
        assert fns[1].end_line == 7

    def test_complexity_per_function(self):
        source = "def simple(x):\n    return x\n\ndef branchy(x):\n    if x:\n        return 1\n    return 0"
        fns = extract_functions(source)
        assert fns[0].complexity == 1
        assert fns[1].complexity == 2

    def test_class_methods(self):
        source = (
            "class Foo:\n"
            "    def bar(self):\n"
            "        return 1\n"
            "    def baz(self, x):\n"
            "        if x:\n"
            "            return x\n"
            "        return 0"
        )
        fns = extract_functions(source)
        assert len(fns) == 2
        assert fns[0].name == "Foo.bar"
        assert fns[0].complexity == 1
        assert fns[1].name == "Foo.baz"
        assert fns[1].complexity == 2

    def test_nested_function_not_extracted(self):
        source = (
            "def outer(x):\n"
            "    def inner(y):\n"
            "        return y\n"
            "    return inner(x)"
        )
        fns = extract_functions(source)
        assert len(fns) == 1
        assert fns[0].name == "outer"

    def test_no_nested_complexity_attribution(self):
        source = (
            "def alpha(x):\n"
            "    if x:\n"
            "        return 1\n"
            "    return 0\n\n"
            "CONSTANT = [\n"
            "    x for x in range(10) if x > 5\n"
            "]\n\n"
            "def omega(y):\n"
            "    return y"
        )
        fns = extract_functions(source)
        by_name = {f.name: f for f in fns}
        assert len(fns) == 2
        assert by_name["alpha"].complexity == 2
        assert by_name["omega"].complexity == 1

"""Tests for agent/tools/"""

import pytest

from agent.tools.calculator import CalculatorTool, _safe_eval
from agent.tools.system_info import SystemInfoTool
from agent.tools.base import BaseTool


class TestCalculatorTool:
    @pytest.fixture
    def calc(self):
        return CalculatorTool()

    def test_basic_addition(self, calc):
        assert calc.run(expression="2 + 3") == "5"

    def test_subtraction(self, calc):
        assert calc.run(expression="10 - 4") == "6"

    def test_multiplication(self, calc):
        assert calc.run(expression="6 * 7") == "42"

    def test_division(self, calc):
        assert calc.run(expression="10 / 4") == "2.5"

    def test_floor_division(self, calc):
        assert calc.run(expression="10 // 3") == "3"

    def test_modulo(self, calc):
        assert calc.run(expression="10 % 3") == "1"

    def test_power(self, calc):
        assert calc.run(expression="2 ** 10") == "1024"

    def test_unary_negation(self, calc):
        assert calc.run(expression="-5") == "-5"

    def test_combined_expression(self, calc):
        result = calc.run(expression="(2 + 3) * 4 - 1")
        assert result == "19"

    def test_zero_division(self, calc):
        result = calc.run(expression="1 / 0")
        assert "Division by zero" in result

    def test_invalid_expression(self, calc):
        result = calc.run(expression="import os")
        assert "⚠️" in result

    def test_empty_expression(self, calc):
        result = calc.run(expression="")
        assert "⚠️" in result

    def test_no_expression_kwarg(self, calc):
        result = calc.run()
        assert "⚠️" in result

    def test_tool_name_and_description(self, calc):
        assert calc.name == "calculator"
        assert "arithmetic" in calc.description.lower()

    def test_schema(self, calc):
        schema = calc.get_schema()
        assert schema["name"] == "calculator"
        assert "description" in schema


class TestSystemInfoTool:
    @pytest.fixture
    def sys_tool(self):
        return SystemInfoTool()

    def test_returns_string(self, sys_tool):
        result = sys_tool.run()
        assert isinstance(result, str)

    def test_contains_os_info(self, sys_tool):
        result = sys_tool.run()
        assert "OS:" in result or "System" in result

    def test_tool_name(self, sys_tool):
        assert sys_tool.name == "system_info"

    def test_is_base_tool(self, sys_tool):
        assert isinstance(sys_tool, BaseTool)


class TestBaseTool:
    def test_abstract_cannot_instantiate(self):
        with pytest.raises(TypeError):
            BaseTool()  # type: ignore

    def test_concrete_subclass(self):
        class MyTool(BaseTool):
            name = "my_tool"
            description = "A test tool"

            def run(self, **kwargs):
                return "ok"

        t = MyTool()
        assert t.run() == "ok"
        assert repr(t) == "<Tool name='my_tool'>"

"""Tests for NewQuizHandler._generate_formula_solutions() — formula evaluation."""

import pytest
from handlers.new_quiz_handler import NewQuizHandler


handler = NewQuizHandler()


class TestBasicFormulas:

    def test_simple_addition(self):
        solutions = handler._generate_formula_solutions(
            "A + B",
            [{"name": "A", "min": 1, "max": 5, "precision": 0},
             {"name": "B", "min": 1, "max": 5, "precision": 0}],
            count=3,
        )
        assert len(solutions) == 3
        for s in solutions:
            a = float(next(i["value"] for i in s["inputs"] if i["name"] == "A"))
            b = float(next(i["value"] for i in s["inputs"] if i["name"] == "B"))
            assert float(s["output"]) == a + b

    def test_multiplication(self):
        solutions = handler._generate_formula_solutions(
            "F * 1000 / A",
            [{"name": "F", "min": 10, "max": 100, "precision": 0},
             {"name": "A", "min": 50, "max": 500, "precision": 0}],
            count=5,
        )
        assert len(solutions) == 5
        for s in solutions:
            f = float(next(i["value"] for i in s["inputs"] if i["name"] == "F"))
            a = float(next(i["value"] for i in s["inputs"] if i["name"] == "A"))
            expected = round(f * 1000 / a, 4)
            assert float(s["output"]) == expected


class TestEvenDistribution:

    def test_even_spacing(self):
        solutions = handler._generate_formula_solutions(
            "x",
            [{"name": "x", "min": 0, "max": 10, "precision": 0}],
            count=3,
            distribution="even",
        )
        values = [float(s["inputs"][0]["value"]) for s in solutions]
        assert values == [0.0, 5.0, 10.0]

    def test_single_value_even(self):
        solutions = handler._generate_formula_solutions(
            "x",
            [{"name": "x", "min": 5, "max": 5, "precision": 0}],
            count=1,
            distribution="even",
        )
        assert len(solutions) == 1
        assert float(solutions[0]["inputs"][0]["value"]) == 5.0


class TestPrecision:

    def test_integer_precision(self):
        solutions = handler._generate_formula_solutions(
            "x",
            [{"name": "x", "min": 0, "max": 100, "precision": 0}],
            count=5,
        )
        for s in solutions:
            val = s["inputs"][0]["value"]
            assert "." in val  # float representation
            assert float(val) == int(float(val))  # but whole number

    def test_decimal_precision(self):
        solutions = handler._generate_formula_solutions(
            "x",
            [{"name": "x", "min": 0, "max": 1, "precision": 2}],
            count=5,
            distribution="random",
        )
        for s in solutions:
            val = s["inputs"][0]["value"]
            parts = val.split(".")
            if len(parts) == 2:
                assert len(parts[1]) <= 2


class TestOutputFormat:

    def test_solution_structure(self):
        solutions = handler._generate_formula_solutions(
            "x + 1",
            [{"name": "x", "min": 0, "max": 10, "precision": 0}],
            count=2,
        )
        for s in solutions:
            assert "inputs" in s
            assert "output" in s
            assert isinstance(s["inputs"], list)
            assert isinstance(s["output"], str)
            for inp in s["inputs"]:
                assert "name" in inp
                assert "value" in inp


class TestErrorHandling:

    def test_division_by_zero_raises(self):
        """Formula producing an error should raise ValueError."""
        with pytest.raises(ValueError):
            handler._generate_formula_solutions(
                "1 / x",
                [{"name": "x", "min": 0, "max": 0, "precision": 0}],
                count=1,
                distribution="even",
            )

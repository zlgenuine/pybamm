#
# Tests for the Function classes
#
import pybamm

import unittest
import numpy as np
from scipy.interpolate import interp1d


def test_function(arg):
    return arg + arg


def test_multi_var_function(arg1, arg2):
    return arg1 + arg2


def test_multi_var_function_cube(arg1, arg2):
    return arg1 + arg2 ** 3


class TestFunction(unittest.TestCase):
    def test_number_input(self):
        # with numbers
        log = pybamm.log(10)
        self.assertIsInstance(log.children[0], pybamm.Scalar)
        self.assertEqual(log.evaluate(), np.log(10))

        summ = pybamm.Function(test_multi_var_function, 1, 2)
        self.assertIsInstance(summ.children[0], pybamm.Scalar)
        self.assertIsInstance(summ.children[1], pybamm.Scalar)
        self.assertEqual(summ.evaluate(), 3)

    def test_function_of_one_variable(self):
        a = pybamm.Symbol("a")
        funca = pybamm.Function(test_function, a)
        self.assertEqual(funca.name, "function (test_function)")
        self.assertEqual(funca.children[0].name, a.name)

        b = pybamm.Scalar(1)
        sina = pybamm.Function(np.sin, b)
        self.assertEqual(sina.evaluate(), np.sin(1))
        self.assertEqual(sina.name, "function ({})".format(np.sin.__name__))

        c = pybamm.Vector(np.linspace(0, 1))
        cosb = pybamm.Function(np.cos, c)
        np.testing.assert_array_equal(cosb.evaluate(), np.cos(c.evaluate()))

        var = pybamm.StateVector(slice(0, 100))
        y = np.linspace(0, 1, 100)[:, np.newaxis]
        logvar = pybamm.Function(np.log1p, var)
        np.testing.assert_array_equal(logvar.evaluate(y=y), np.log1p(y))

        # use known_evals
        np.testing.assert_array_equal(
            logvar.evaluate(y=y, known_evals={})[0], np.log1p(y)
        )

    def test_diff(self):
        a = pybamm.StateVector(slice(0, 1))
        b = pybamm.StateVector(slice(1, 2))
        y = np.array([5])
        func = pybamm.Function(test_function, a)
        self.assertEqual(func.diff(a).evaluate(y=y), 2)
        self.assertEqual(func.diff(func).evaluate(), 1)
        func = pybamm.sin(a)
        self.assertEqual(func.evaluate(y=y), np.sin(a.evaluate(y=y)))
        self.assertEqual(func.diff(a).evaluate(y=y), np.cos(a.evaluate(y=y)))
        func = pybamm.exp(a)
        self.assertEqual(func.evaluate(y=y), np.exp(a.evaluate(y=y)))
        self.assertEqual(func.diff(a).evaluate(y=y), np.exp(a.evaluate(y=y)))

        # multiple variables
        func = pybamm.Function(test_multi_var_function, 4 * a, 3 * a)
        self.assertEqual(func.diff(a).evaluate(y=y), 7)
        func = pybamm.Function(test_multi_var_function, 4 * a, 3 * b)
        self.assertEqual(func.diff(a).evaluate(y=np.array([5, 6])), 4)
        self.assertEqual(func.diff(b).evaluate(y=np.array([5, 6])), 3)
        func = pybamm.Function(test_multi_var_function_cube, 4 * a, 3 * b)
        self.assertEqual(func.diff(a).evaluate(y=np.array([5, 6])), 4)
        self.assertEqual(
            func.diff(b).evaluate(y=np.array([5, 6])), 3 * 3 * (3 * 6) ** 2
        )

        # exceptions
        func = pybamm.Function(
            test_multi_var_function_cube, 4 * a, 3 * b, derivative="derivative"
        )
        with self.assertRaises(ValueError):
            func.diff(a)

    def test_function_of_multiple_variables(self):
        a = pybamm.Variable("a")
        b = pybamm.Parameter("b")
        func = pybamm.Function(test_multi_var_function, a, b)
        self.assertEqual(func.name, "function (test_multi_var_function)")
        self.assertEqual(func.children[0].name, a.name)
        self.assertEqual(func.children[1].name, b.name)

        # test eval and diff
        a = pybamm.StateVector(slice(0, 1))
        b = pybamm.StateVector(slice(1, 2))
        y = np.array([5, 2])
        func = pybamm.Function(test_multi_var_function, a, b)

        self.assertEqual(func.evaluate(y=y), 7)
        self.assertEqual(func.diff(a).evaluate(y=y), 1)
        self.assertEqual(func.diff(b).evaluate(y=y), 1)
        self.assertEqual(func.diff(func).evaluate(), 1)

    def test_exceptions(self):
        a = pybamm.Variable("a", domain="something")
        b = pybamm.Variable("b", domain="something else")
        with self.assertRaises(pybamm.DomainError):
            pybamm.Function(test_multi_var_function, a, b)

    def test_function_unnamed(self):
        t = np.linspace(0, 1)
        entries = 2 * t
        interpfun = interp1d(t, entries)
        fun = pybamm.Function(interpfun, pybamm.t)
        self.assertEqual(
            fun.name, "function (<class 'scipy.interpolate.interpolate.interp1d'>)"
        )


class TestSpecificFunctions(unittest.TestCase):
    def test_arcsinh(self):
        a = pybamm.Scalar(3)
        fun = pybamm.arcsinh(a)
        self.assertIsInstance(fun, pybamm.Arcsinh)
        self.assertEqual(fun.evaluate(), np.arcsinh(3))
        h = 0.0000001
        self.assertAlmostEqual(
            fun.diff(a).evaluate(),
            (pybamm.arcsinh(pybamm.Scalar(3 + h)).evaluate() - fun.evaluate()) / h,
            places=5,
        )

    def test_cos(self):
        a = pybamm.Scalar(3)
        fun = pybamm.cos(a)
        self.assertIsInstance(fun, pybamm.Cos)
        self.assertEqual(fun.children[0].id, a.id)
        self.assertEqual(fun.evaluate(), np.cos(3))
        h = 0.0000001
        self.assertAlmostEqual(
            fun.diff(a).evaluate(),
            (pybamm.cos(pybamm.Scalar(3 + h)).evaluate() - fun.evaluate()) / h,
            places=5,
        )

        # test simplify
        y = pybamm.StateVector(slice(0, 1))
        fun = pybamm.cos(y)
        self.assertEqual(fun.id, fun.simplify().id)

    def test_cosh(self):
        a = pybamm.Scalar(3)
        fun = pybamm.cosh(a)
        self.assertIsInstance(fun, pybamm.Cosh)
        self.assertEqual(fun.children[0].id, a.id)
        self.assertEqual(fun.evaluate(), np.cosh(3))
        h = 0.0000001
        self.assertAlmostEqual(
            fun.diff(a).evaluate(),
            (pybamm.cosh(pybamm.Scalar(3 + h)).evaluate() - fun.evaluate()) / h,
            places=5,
        )

    def test_exp(self):
        a = pybamm.Scalar(3)
        fun = pybamm.exp(a)
        self.assertIsInstance(fun, pybamm.Exponential)
        self.assertEqual(fun.children[0].id, a.id)
        self.assertEqual(fun.evaluate(), np.exp(3))
        h = 0.0000001
        self.assertAlmostEqual(
            fun.diff(a).evaluate(),
            (pybamm.exp(pybamm.Scalar(3 + h)).evaluate() - fun.evaluate()) / h,
            places=5,
        )

    def test_log(self):
        a = pybamm.Scalar(3)
        fun = pybamm.log(a)
        self.assertEqual(fun.evaluate(), np.log(3))
        h = 0.0000001
        self.assertAlmostEqual(
            fun.diff(a).evaluate(),
            (pybamm.log(pybamm.Scalar(3 + h)).evaluate() - fun.evaluate()) / h,
            places=5,
        )

        # Base 10
        fun = pybamm.log10(a)
        self.assertEqual(fun.evaluate(), np.log10(3))
        h = 0.0000001
        self.assertAlmostEqual(
            fun.diff(a).evaluate(),
            (pybamm.log10(pybamm.Scalar(3 + h)).evaluate() - fun.evaluate()) / h,
            places=5,
        )

    def test_max(self):
        a = pybamm.Vector(np.array([1, 2, 3]))
        fun = pybamm.max(a)
        self.assertIsInstance(fun, pybamm.Function)
        self.assertEqual(fun.evaluate(), 3)

    def test_min(self):
        a = pybamm.Vector(np.array([1, 2, 3]))
        fun = pybamm.min(a)
        self.assertIsInstance(fun, pybamm.Function)
        self.assertEqual(fun.evaluate(), 1)

    def test_sin(self):
        a = pybamm.Scalar(3)
        fun = pybamm.sin(a)
        self.assertIsInstance(fun, pybamm.Sin)
        self.assertEqual(fun.children[0].id, a.id)
        self.assertEqual(fun.evaluate(), np.sin(3))
        h = 0.0000001
        self.assertAlmostEqual(
            fun.diff(a).evaluate(),
            (pybamm.sin(pybamm.Scalar(3 + h)).evaluate() - fun.evaluate()) / h,
            places=5,
        )

    def test_sinh(self):
        a = pybamm.Scalar(3)
        fun = pybamm.sinh(a)
        self.assertIsInstance(fun, pybamm.Sinh)
        self.assertEqual(fun.children[0].id, a.id)
        self.assertEqual(fun.evaluate(), np.sinh(3))
        h = 0.0000001
        self.assertAlmostEqual(
            fun.diff(a).evaluate(),
            (pybamm.sinh(pybamm.Scalar(3 + h)).evaluate() - fun.evaluate()) / h,
            places=5,
        )

    def test_sqrt(self):
        a = pybamm.Scalar(3)
        fun = pybamm.sqrt(a)
        self.assertIsInstance(fun, pybamm.Sqrt)
        self.assertEqual(fun.evaluate(), np.sqrt(3))
        h = 0.0000001
        self.assertAlmostEqual(
            fun.diff(a).evaluate(),
            (pybamm.sqrt(pybamm.Scalar(3 + h)).evaluate() - fun.evaluate()) / h,
            places=5,
        )

    def test_tanh(self):
        a = pybamm.Scalar(3)
        fun = pybamm.tanh(a)
        self.assertEqual(fun.evaluate(), np.tanh(3))
        h = 0.0000001
        self.assertAlmostEqual(
            fun.diff(a).evaluate(),
            (pybamm.tanh(pybamm.Scalar(3 + h)).evaluate() - fun.evaluate()) / h,
            places=5,
        )


if __name__ == "__main__":
    print("Add -v for more debug output")
    import sys

    if "-v" in sys.argv:
        debug = True
    pybamm.settings.debug_mode = True
    unittest.main()

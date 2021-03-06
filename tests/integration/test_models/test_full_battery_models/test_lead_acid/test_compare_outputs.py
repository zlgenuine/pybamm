#
# Tests for the asymptotic convergence of the simplified models
#
import pybamm
import numpy as np
import unittest
from tests import StandardOutputComparison


class TestCompareOutputs(unittest.TestCase):
    def test_compare_averages_asymptotics(self):
        """
        Check that the average value of certain variables is constant across submodels
        """
        # load models
        models = [
            pybamm.lead_acid.LOQS(),
            pybamm.lead_acid.Composite(),
            pybamm.lead_acid.Full(),
        ]

        # load parameter values (same for all models)
        param = models[0].default_parameter_values
        param.update({"Typical current [A]": 1})
        for model in models:
            param.process_model(model)

        # set mesh
        var = pybamm.standard_spatial_vars
        var_pts = {var.x_n: 10, var.x_s: 10, var.x_p: 10}

        # discretise models
        discs = {}
        for model in models:
            geometry = model.default_geometry
            param.process_geometry(geometry)
            mesh = pybamm.Mesh(geometry, model.default_submesh_types, var_pts)
            disc = pybamm.Discretisation(mesh, model.default_spatial_methods)
            disc.process_model(model)
            discs[model] = disc

        # solve model
        solutions = {}
        t_eval = np.linspace(0, 1, 100)
        for i, model in enumerate(models):
            solution = model.default_solver.solve(model, t_eval)
            solutions[model] = solution

        # test averages
        comparison = StandardOutputComparison(models, discs, solutions)
        comparison.test_averages()

    def test_compare_outputs_capacitance(self):
        """
        Check that the leading-order model solution converges linearly in C_e to the
        full model solution
        """
        # load models
        options = [
            {"surface form": cap} for cap in [False, "differential", "algebraic"]
        ]
        model_combos = [
            ([pybamm.lead_acid.LOQS(opt) for opt in options]),
            ([pybamm.lead_acid.Full(opt) for opt in options]),
        ]

        for models in model_combos:
            # load parameter values (same for all models)
            param = models[0].default_parameter_values
            param.update({"Typical current [A]": 1})
            for model in models:
                param.process_model(model)

            # set mesh
            var = pybamm.standard_spatial_vars
            var_pts = {var.x_n: 5, var.x_s: 5, var.x_p: 5}

            # discretise models
            discs = {}
            for model in models:
                geometry = model.default_geometry
                param.process_geometry(geometry)
                mesh = pybamm.Mesh(geometry, model.default_submesh_types, var_pts)
                disc = pybamm.Discretisation(mesh, model.default_spatial_methods)
                disc.process_model(model)
                discs[model] = disc

            # solve model
            solutions = {}
            t_eval = np.linspace(0, 1, 100)
            for i, model in enumerate(models):
                solution = model.default_solver.solve(model, t_eval)
                solutions[model] = solution

            # compare outputs
            comparison = StandardOutputComparison(models, discs, solutions)
            comparison.test_all(skip_first_timestep=True)


if __name__ == "__main__":
    print("Add -v for more debug output")
    import sys

    if "-v" in sys.argv:
        debug = True
    unittest.main()

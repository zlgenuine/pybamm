import pybamm
import numpy as np
import unittest


class TestSimulation(unittest.TestCase):
    def test_basic_ops(self):

        model = pybamm.lithium_ion.SPM()
        sim = pybamm.Simulation(model)

        self.assertEqual(model.__class__, sim._model_class)
        self.assertEqual(model.options, sim._model_options)

        # check that the model is unprocessed
        self.assertEqual(sim._mesh, None)
        self.assertEqual(sim._disc, None)
        for val in list(sim.model.rhs.values()):
            self.assertTrue(val.has_symbol_of_classes(pybamm.Parameter))
            self.assertFalse(val.has_symbol_of_classes(pybamm.Matrix))

        sim.set_parameters()
        self.assertEqual(sim._mesh, None)
        self.assertEqual(sim._disc, None)
        for val in list(sim.model_with_set_params.rhs.values()):
            self.assertFalse(val.has_symbol_of_classes(pybamm.Parameter))
            self.assertFalse(val.has_symbol_of_classes(pybamm.Matrix))

        sim.build()
        self.assertFalse(sim._mesh is None)
        self.assertFalse(sim._disc is None)
        for val in list(sim.built_model.rhs.values()):
            self.assertFalse(val.has_symbol_of_classes(pybamm.Parameter))
            self.assertTrue(val.has_symbol_of_classes(pybamm.Matrix))

        sim.reset()
        sim.set_parameters()
        self.assertEqual(sim._mesh, None)
        self.assertEqual(sim._disc, None)
        self.assertEqual(sim.built_model, None)

        for val in list(sim.model_with_set_params.rhs.values()):
            self.assertFalse(val.has_symbol_of_classes(pybamm.Parameter))
            self.assertFalse(val.has_symbol_of_classes(pybamm.Matrix))

        sim.build()
        sim.reset()
        self.assertEqual(sim._mesh, None)
        self.assertEqual(sim._disc, None)
        self.assertEqual(sim.model_with_set_params, None)
        self.assertEqual(sim.built_model, None)
        for val in list(sim.model.rhs.values()):
            self.assertTrue(val.has_symbol_of_classes(pybamm.Parameter))
            self.assertFalse(val.has_symbol_of_classes(pybamm.Matrix))

    def test_solve(self):

        sim = pybamm.Simulation(pybamm.lithium_ion.SPM())
        sim.solve()
        self.assertFalse(sim._solution is None)
        for val in list(sim.built_model.rhs.values()):
            self.assertFalse(val.has_symbol_of_classes(pybamm.Parameter))
            self.assertTrue(val.has_symbol_of_classes(pybamm.Matrix))

        sim.reset()
        self.assertEqual(sim.model_with_set_params, None)
        self.assertEqual(sim.built_model, None)
        for val in list(sim.model.rhs.values()):
            self.assertTrue(val.has_symbol_of_classes(pybamm.Parameter))
            self.assertFalse(val.has_symbol_of_classes(pybamm.Matrix))

        self.assertEqual(sim._solution, None)

        # test solve without check
        sim.reset()
        sim.solve(check_model=False)
        for val in list(sim.built_model.rhs.values()):
            self.assertFalse(val.has_symbol_of_classes(pybamm.Parameter))
            self.assertTrue(val.has_symbol_of_classes(pybamm.Matrix))

    def test_reuse_commands(self):

        sim = pybamm.Simulation(pybamm.lithium_ion.SPM())

        sim.set_parameters()
        sim.set_parameters()

        sim.build()
        sim.build()

        sim.solve()
        sim.solve()

        sim.build()
        sim.solve()
        sim.set_parameters()

    def test_specs(self):
        # test can rebuild after setting specs
        sim = pybamm.Simulation(pybamm.lithium_ion.SPM())
        sim.build()

        model_options = {"thermal": "lumped"}
        sim.specs(model_options=model_options)
        sim.build()
        self.assertEqual(sim.model.options["thermal"], "lumped")

        params = sim.parameter_values
        # normally is 0.0001
        params.update({"Negative electrode thickness [m]": 0.0002})
        sim.specs(parameter_values=params)

        self.assertEqual(
            sim.parameter_values["Negative electrode thickness [m]"], 0.0002
        )
        sim.build()

        geometry = sim.unprocessed_geometry
        custom_geometry = {}
        x_n = pybamm.standard_spatial_vars.x_n
        custom_geometry["negative electrode"] = {
            "primary": {
                x_n: {"min": pybamm.Scalar(0), "max": pybamm.geometric_parameters.l_n}
            }
        }
        geometry.update(custom_geometry)
        sim.specs(geometry=geometry)
        sim.build()

        var_pts = sim.var_pts
        var_pts[pybamm.standard_spatial_vars.x_n] = 5
        sim.specs(var_pts=var_pts)
        sim.build()

        spatial_methods = sim.spatial_methods
        # nothing to change this to at the moment but just reload in
        sim.specs(spatial_methods=spatial_methods)
        sim.build()

    def test_set_crate(self):
        sim = pybamm.Simulation(pybamm.lithium_ion.SPM(), C_rate=2)
        self.assertEqual(sim.parameter_values["C-rate"], 2)
        sim.specs(C_rate=3)
        self.assertEqual(sim.parameter_values["C-rate"], 3)

    def test_set_defaults(self):
        sim = pybamm.Simulation(pybamm.lithium_ion.SPM())

        model_options = {"thermal": "x-full"}
        submesh_types = {
            "Negative particle": pybamm.MeshGenerator(pybamm.Exponential1DSubMesh)
        }
        solver = pybamm.BaseSolver()
        quick_plot_vars = ["Negative particle surface concentration"]
        sim.specs(
            model_options=model_options,
            submesh_types=submesh_types,
            solver=solver,
            quick_plot_vars=quick_plot_vars,
        )

        sim.set_defaults()

        self.assertEqual(sim.model_options["thermal"], "x-full")
        self.assertEqual(
            sim.submesh_types["negative particle"].submesh_type, pybamm.Uniform1DSubMesh
        )
        self.assertEqual(sim.quick_plot_vars, None)
        self.assertIsInstance(sim.solver, pybamm.ScipySolver)

    def test_get_variable_array(self):

        sim = pybamm.Simulation(pybamm.lithium_ion.SPM())
        sim.solve()

        phi_s_n = sim.get_variable_array("Negative electrode potential")

        self.assertIsInstance(phi_s_n, np.ndarray)

        c_s_n_surf, c_e = sim.get_variable_array(
            "Negative particle surface concentration", "Electrolyte concentration"
        )

        self.assertIsInstance(c_s_n_surf, np.ndarray)
        self.assertIsInstance(c_e, np.ndarray)

    def test_set_external_variable(self):
        model_options = {
            "thermal": "x-lumped",
            "external submodels": ["thermal"],
        }
        model = pybamm.lithium_ion.SPMe(model_options)
        sim = pybamm.Simulation(model)

        T_av = 0

        dt = 0.001

        external_variables = {"X-averaged cell temperature": T_av}
        sim.step(dt, external_variables=external_variables)

    def test_step(self):

        dt = 0.001
        sim = pybamm.Simulation(pybamm.lithium_ion.SPM())
        sim.step(dt)  # 1 step stores first two points
        self.assertEqual(sim.solution.t.size, 2)
        self.assertEqual(sim.solution.y[0, :].size, 2)
        self.assertEqual(sim.solution.t[0], 0)
        self.assertEqual(sim.solution.t[1], dt)
        sim.step(dt)  # automatically append the next step
        self.assertEqual(sim.solution.t.size, 3)
        self.assertEqual(sim.solution.y[0, :].size, 3)
        self.assertEqual(sim.solution.t[0], 0)
        self.assertEqual(sim.solution.t[1], dt)
        self.assertEqual(sim.solution.t[2], 2 * dt)
        sim.step(dt, save=False)  # now only store the two end step points
        self.assertEqual(sim.solution.t.size, 2)
        self.assertEqual(sim.solution.y[0, :].size, 2)
        self.assertEqual(sim.solution.t[0], 2 * dt)
        self.assertEqual(sim.solution.t[1], 3 * dt)

    def test_save_load(self):
        model = pybamm.lead_acid.LOQS()
        model.use_jacobian = True
        sim = pybamm.Simulation(model)

        sim.save("test.pickle")
        sim_load = pybamm.load_sim("test.pickle")
        self.assertEqual(sim.model.name, sim_load.model.name)

        # save after solving
        sim.solve()
        sim.save("test.pickle")
        sim_load = pybamm.load_sim("test.pickle")
        self.assertEqual(sim.model.name, sim_load.model.name)

        # with python formats
        model.convert_to_format = None
        sim = pybamm.Simulation(model)
        sim.solve()
        sim.save("test.pickle")
        model.convert_to_format = "python"
        sim = pybamm.Simulation(model)
        sim.solve()
        with self.assertRaisesRegex(
            NotImplementedError, "Cannot save simulation if model format is python"
        ):
            sim.save("test.pickle")

    def test_save_load_dae(self):
        model = pybamm.lead_acid.LOQS({"surface form": "algebraic"})
        model.use_jacobian = True
        sim = pybamm.Simulation(model)

        # save after solving
        sim.solve()
        sim.save("test.pickle")
        sim_load = pybamm.load_sim("test.pickle")
        self.assertEqual(sim.model.name, sim_load.model.name)

        # with python format
        model.convert_to_format = None
        sim = pybamm.Simulation(model)
        sim.solve()
        sim.save("test.pickle")

        # with Casadi solver
        sim = pybamm.Simulation(model, solver=pybamm.CasadiSolver())
        sim.solve()
        sim.save("test.pickle")
        sim_load = pybamm.load_sim("test.pickle")
        self.assertEqual(sim.model.name, sim_load.model.name)

    @unittest.skipIf(not pybamm.have_idaklu(), "idaklu solver is not installed")
    def test_save_load_klu(self):
        model = pybamm.lead_acid.LOQS({"surface form": "algebraic"})
        model.use_jacobian = True
        # with KLU solver
        sim = pybamm.Simulation(model, solver=pybamm.IDAKLUSolver())
        sim.solve()
        sim.save("test.pickle")
        sim_load = pybamm.load_sim("test.pickle")
        self.assertEqual(sim.model.name, sim_load.model.name)

    def test_set_defaults2(self):
        model = pybamm.lithium_ion.SPM()

        # make simulation with silly options (should this be allowed?)
        sim = pybamm.Simulation(
            model,
            geometry=1,
            parameter_values=1,
            submesh_types=1,
            var_pts=1,
            spatial_methods=1,
            solver=1,
            quick_plot_vars=1,
        )

        # reset and check
        sim.set_defaults()
        # Not sure of best way to test nested dicts?
        # self.geometry = model.default_geometry
        self.assertEqual(sim._parameter_values, model.default_parameter_values)
        for domain, submesh in model.default_submesh_types.items():
            self.assertEqual(
                sim._submesh_types[domain].submesh_type, submesh.submesh_type
            )
        self.assertEqual(sim._var_pts, model.default_var_pts)
        for domain, method in model.default_spatial_methods.items():
            self.assertIsInstance(sim._spatial_methods[domain], type(method))
        self.assertIsInstance(sim._solver, type(model.default_solver))
        self.assertEqual(sim._quick_plot_vars, None)

    def test_plot(self):
        sim = pybamm.Simulation(pybamm.lithium_ion.SPM())

        # test exception if not solved
        with self.assertRaises(ValueError):
            sim.plot()

        # now solve and plot
        t_eval = np.linspace(0, 0.01, 5)
        sim.solve(t_eval=t_eval)
        sim.plot(testing=True)


if __name__ == "__main__":
    print("Add -v for more debug output")
    import sys

    if "-v" in sys.argv:
        debug = True
    unittest.main()

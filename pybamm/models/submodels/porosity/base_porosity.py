#
# Base class for porosity
#
import pybamm


class BaseModel(pybamm.BaseSubModel):
    """Base class for porosity

    Parameters
    ----------
    param : parameter class
        The parameters to use for this submodel


    **Extends:** :class:`pybamm.BaseSubModel`
    """

    def __init__(self, param):
        super().__init__(param)

    def _get_standard_porosity_variables(self, eps, set_leading_order=False):

        eps_n, eps_s, eps_p = eps.orphans

        variables = {
            "Porosity": eps,
            "Negative electrode porosity": eps_n,
            "Separator porosity": eps_s,
            "Positive electrode porosity": eps_p,
            "X-averaged negative electrode porosity": pybamm.x_average(eps_n),
            "X-averaged separator porosity": pybamm.x_average(eps_s),
            "X-averaged positive electrode porosity": pybamm.x_average(eps_p),
        }

        # activate material volume fractions
        eps_solid_n = 1 - eps_n - self.param.epsilon_inactive_n
        eps_solid_s = 1 - eps_s - self.param.epsilon_inactive_s
        eps_solid_p = 1 - eps_p - self.param.epsilon_inactive_p
        eps_solid = pybamm.Concatenation(eps_solid_n, eps_solid_s, eps_solid_p)

        am = "active material volume fraction"
        variables.update(
            {
                am.capitalize(): eps_solid,
                "Negative electrode " + am: eps_solid_n,
                "Separator " + am: eps_solid,
                "Positive electrode " + am: eps_solid_p,
                "X-averaged negative electrode " + am: pybamm.x_average(eps_solid_n),
                "X-averaged separator " + am: pybamm.x_average(eps_solid),
                "X-averaged positive electrode " + am: pybamm.x_average(eps_solid_p),
            }
        )

        if set_leading_order is True:
            leading_order_variables = {
                "Leading-order " + name.lower(): var for name, var in variables.items()
            }
            variables.update(leading_order_variables)

        return variables

    def _get_standard_porosity_change_variables(self, deps_dt, set_leading_order=False):

        deps_n_dt, deps_s_dt, deps_p_dt = deps_dt.orphans

        variables = {
            "Porosity change": deps_dt,
            "Negative electrode porosity change": deps_n_dt,
            "Separator porosity change": deps_s_dt,
            "Positive electrode porosity change": deps_p_dt,
            "X-averaged porosity change": pybamm.x_average(deps_dt),
            "X-averaged negative electrode porosity change": pybamm.x_average(
                deps_n_dt
            ),
            "X-averaged separator porosity change": pybamm.x_average(deps_s_dt),
            "X-averaged positive electrode porosity change": pybamm.x_average(
                deps_p_dt
            ),
        }

        if set_leading_order is True:
            variables.update(
                {
                    "Leading-order x-averaged "
                    + "negative electrode porosity change": pybamm.x_average(deps_n_dt),
                    "Leading-order x-averaged "
                    + "separator porosity change": pybamm.x_average(deps_s_dt),
                    "Leading-order x-averaged "
                    + "positive electrode porosity change": pybamm.x_average(deps_p_dt),
                }
            )

        return variables

    def set_events(self, variables):
        eps_n = variables["Negative electrode porosity"]
        eps_p = variables["Positive electrode porosity"]
        self.events["Zero negative electrode porosity cut-off"] = pybamm.min(eps_n)
        self.events["Max negative electrode porosity cut-off"] = pybamm.max(eps_n) - 1
        self.events["Zero positive electrode porosity cut-off"] = pybamm.min(eps_p)
        self.events["Max positive electrode porosity cut-off"] = pybamm.max(eps_p) - 1

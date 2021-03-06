#
# Base class for electrode submodels
#
import pybamm


class BaseElectrode(pybamm.BaseSubModel):
    """Base class for electrode submodels.

    Parameters
    ----------
    param : parameter class
        The parameters to use for this submodel
    domain : str
        Either 'Negative' or 'Positive'
    set_positive_potential :  bool, optional
        If True the battery model sets the positve potential based on the current.
        If False, the potential is specified by the user. Default is True.
    **Extends:** :class:`pybamm.BaseSubModel`
    """

    def __init__(self, param, domain, reactions=None, set_positive_potential=True):
        super().__init__(param, domain, reactions)
        self.set_positive_potential = set_positive_potential

    def _get_standard_potential_variables(self, phi_s):
        """
        A private function to obtain the standard variables which
        can be derived from the potential in the electrode.

        Parameters
        ----------
        phi_s : :class:`pybamm.Symbol`
            The potential in the electrode.

        Returns
        -------
        variables : dict
            The variables which can be derived from the potential in the
            electrode.
        """
        param = self.param
        phi_s_av = pybamm.x_average(phi_s)

        if self.domain == "Negative":
            phi_s_dim = param.potential_scale * phi_s
            phi_s_av_dim = param.potential_scale * phi_s_av
            delta_phi_s = phi_s

        elif self.domain == "Positive":
            phi_s_dim = param.U_p_ref - param.U_n_ref + param.potential_scale * phi_s
            phi_s_av_dim = (
                param.U_p_ref - param.U_n_ref + param.potential_scale * phi_s_av
            )

            v = pybamm.boundary_value(phi_s, "right")
            delta_phi_s = phi_s - v
        delta_phi_s_av = pybamm.x_average(delta_phi_s)
        delta_phi_s_dim = delta_phi_s * param.potential_scale
        delta_phi_s_av_dim = delta_phi_s_av * param.potential_scale

        variables = {
            self.domain + " electrode potential": phi_s,
            self.domain + " electrode potential [V]": phi_s_dim,
            "X-averaged " + self.domain.lower() + " electrode potential": phi_s_av,
            "X-averaged "
            + self.domain.lower()
            + " electrode potential [V]": phi_s_av_dim,
            self.domain + " electrode ohmic losses": delta_phi_s,
            self.domain + " electrode ohmic losses [V]": delta_phi_s_dim,
            "X-averaged "
            + self.domain.lower()
            + " electrode ohmic losses": delta_phi_s_av,
            "X-averaged "
            + self.domain.lower()
            + " electrode ohmic losses [V]": delta_phi_s_av_dim,
            "Gradient of "
            + self.domain.lower()
            + " electrode potential": pybamm.grad(phi_s),
        }

        return variables

    def _get_standard_current_variables(self, i_s):
        """
        A private function to obtain the standard variables which
        can be derived from the current in the electrode.

        Parameters
        ----------
        i_s : :class:`pybamm.Symbol`
            The current in the electrode.

        Returns
        -------
        variables : dict
            The variables which can be derived from the current in the
            electrode.
        """
        param = self.param

        i_s_dim = param.i_typ * i_s

        variables = {
            self.domain + " electrode current density": i_s,
            self.domain + " electrode current density [A.m-2]": i_s_dim,
        }

        return variables

    def _get_standard_whole_cell_variables(self, variables):
        """
        A private function to obtain the whole-cell versions of the
        current variables.

        Parameters
        ----------
        variables : dict
            The variables in the whole model.

        Returns
        -------
        variables : dict
            The variables in the whole model with the whole-cell
            current variables added.
        """

        i_s_n = variables["Negative electrode current density"]
        i_s_s = pybamm.FullBroadcast(0, ["separator"], "current collector")
        i_s_p = variables["Positive electrode current density"]

        i_s = pybamm.Concatenation(i_s_n, i_s_s, i_s_p)

        if self.set_positive_potential:
            phi_s_p = variables["Positive electrode potential"]
            phi_s_cp = pybamm.boundary_value(phi_s_p, "right")
            variables = {
                "Electrode current density": i_s,
                "Positive current collector potential": phi_s_cp,
            }
        else:
            variables = {"Electrode current density": i_s}

        return variables

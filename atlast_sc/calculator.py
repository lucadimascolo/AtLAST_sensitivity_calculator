import astropy.units as u
import numpy as np
from atlast_sc.atmosphere_params import AtmosphereParams
from atlast_sc.sefd import SEFD
from atlast_sc.system_temperature import SystemTemperature
from atlast_sc.efficiencies import Efficiencies
from atlast_sc.inputs import CalculatedParams
from atlast_sc.inputs import SensitivityCalculatorParameters
from atlast_sc.config import Config


class Calculator:
    """
    Calculator class that provides an interface to the main
    calculator functionality and performs the core calculations
    to determine the output sensitivity or integration time.
    """

    def __init__(self, inputs=None):
        # TODO: provide accessor methods for properties
        # TODO: get a list of properties that are editable and provide setters

        config = Config(inputs)
        # Store the input parameters used to initialise the calculator
        self._calculator_inputs = config.calculation_inputs
        # Use the input values to calculate the parameters
        # used in the calculation
        calculated_params = self._calculate_parameters(self._calculator_inputs)

        # Store all the inputs and calculated params used
        # in the sensitivity and integration time calculations
        self._calculator_params = \
            SensitivityCalculatorParameters(
                calculation_inputs=self._calculator_inputs,
                calculated_params=calculated_params
            )

    def calculate_sensitivity(self, t_int):
        """
        Return sensitivity of telescope (Jansky) for a
        given integration time t_int

        :param t_int: integration time
        :type t_int: astropy.units.Quantity
        :return: sensitivity in Janksy
        :rtype: astropy.units.Quantity
        """
        sensitivity = (
                self.calculator_params['sefd']
                / (self.calculator_params['eta_s']
                   * np.sqrt(
                    self.calculator_params['n_pol']
                    * self.calculator_params['bandwidth']
                    * t_int
                ))
                * np.exp(self.calculator_params['tau_atm'])
        )

        return sensitivity.to(u.Jy)

    def calculate_t_integration(self, sensitivity):
        """
        Return integration time required for some sensitivity to be reached.

        :param sensitivity: required sensitivity in Jansky
        :type sensitivity: astropy.units.Quantity
        :return: integration time in seconds
        :rtype: astropy.units.Quantity
        """

        t_int = ((self.calculator_params['sefd']
                  * np.exp(self.calculator_params['tau_atm']))
                 / (sensitivity * self.calculator_params['eta_s'])) ** 2 \
            / (self.calculator_params['n_pol']
               * self.calculator_params['bandwidth'])

        return t_int.to(u.s)

    @property
    def t_int(self):
        return self._calculator_params.calculation_inputs.t_int

    @t_int.setter
    def t_int(self, value):
        # TODO: Setting this value in the on the inputs feels wrong.
        #  This may be a calculated param
        self._calculator_params.calculation_inputs.t_int = value

    @property
    def sensitivity(self):
        return self._calculator_params.calculation_inputs.sensitivity

    @sensitivity.setter
    def sensitivity(self, value):
        # TODO: Setting this value in the on the inputs feels wrong.
        #  This may be a calculated param
        self._calculator_params.calculation_inputs.sensitivity = value

    @property
    def calculator_params(self):
        """
        Parameters used to perform the calculation
        (input params and calculated params)
        """
        return self._calculator_params.calculator_params()

    @property
    def calculation_inputs(self):
        """
        The parameters used to initialise the calculator
        """
        return self._calculator_inputs

    @classmethod
    def _calculate_parameters(cls, calculation_inputs):
        """
        Performs the calculations required to produce the
        final set of parameters required for the sensitivity
        calculation, and outputs the sensitivity or integration
        time as required.

        :return:
        """

        # TODO: can do better with this...

        # Perform atmospheric model calculation
        atm = AtmosphereParams(
            calculation_inputs.obs_freq,
            calculation_inputs.weather,
            calculation_inputs.elevation
        )

        T_atm = atm.T_atm()
        tau_atm = atm.tau_atm()

        # Perform efficiencies calculation
        eta = Efficiencies(
            calculation_inputs.eta_ill,
            calculation_inputs.eta_q,
            calculation_inputs.eta_spill,
            calculation_inputs.eta_block,
            calculation_inputs.eta_pol,
            calculation_inputs.eta_r
        )

        eta_a = eta.eta_a(calculation_inputs.obs_freq,
                          calculation_inputs.surface_rms)
        eta_s = eta.eta_s()

        # Calculate the system temperature
        T_sys = SystemTemperature(
            calculation_inputs.T_rx,
            calculation_inputs.T_cmb,
            T_atm,
            calculation_inputs.T_amb,
            tau_atm
        ).system_temperature(
            calculation_inputs.g,
            calculation_inputs.eta_eff)

        # Calculate the dish area
        area = np.pi * calculation_inputs.dish_radius ** 2
        # Calculate source equivalent flux density
        sefd = SEFD.calculate(T_sys, area, eta_a)

        return CalculatedParams(tau_atm=tau_atm, T_atm=T_atm, eta_a=eta_a,
                                eta_s=eta_s, T_sys=T_sys, sefd=sefd, area=area)
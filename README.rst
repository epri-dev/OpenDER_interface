=================
OpenDER interface
=================


Introduction
============
This is the interfaces designed for `OpenDER <https://github.com/epri-dev/opender/>`__ model, aiming to establish
connections with power system simulators. Current version offers support for interfacing with OpenDSS.

This package include the following function modules:

* OpenDER interface (OpenDERInterface) with distribution system simulators. Currently the interface to OpenDSS is
  released. The interface to other simulation tool, such as CYME or Synergi is planned.
* Time series charts (TimePlots) to plot simulation results with x-axis as time.
* Steady-state charts (XYPlots) to plot steady-state DER operational status, including voltage-reactive power,
  active power-reactive power, frequency-active power, etc.
* Voltage regulator model (VR_Model) external to the circuit simulation tool to all dynamic / time series simulation

Installation
============
**Users are encouraged and expected to make changes to this package for their usage.**
To encourage modifications and changes to this OpenDER model interface, this package is not currently released as a
package on PyPI.

To use it, please install the package locally using the following command at the root directory, where 'setup.py'
resides. Dependencies will be automatically installed:

    ``pip install -e ./``

Examples
=========
* volt-var: demonstrate plotting capabilities
* OpenDSS_34bus - dynamic simulation: interactions between voltage regulators and DER enter service performance
* OpenDSS_34bus - steady state simulation: comparison between OpenDSS internal inverter model vs OpenDER
* OpenDSS_GFOV - single_isource: dynamic simulation of isource experiencing a ground fault over voltage
* OpenDSS_GFOV - single_vsource: dynamic simulation of vsource experiencing a ground fault over voltage
* OpenDSS_BESS_PV - 15min time series simulation using BESS for PV power peak shaving



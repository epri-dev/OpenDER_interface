=================
OpenDER interface
=================



Introduction
============
This is the interfaces designed for `OpenDER <https://github.com/epri-dev/opender/>`__ model, aiming to establish
connections with power system simulators. Current version offers support for interfacing with OpenDSS.

Modules
=======
This project include the following function modules:

* OpenDER interface with power system simulators
* Voltage regulator model (VR_Model) for deriving VR taps
* Plot function for time series chart
* Plot function for steady-state charts, including voltage-reactive power, active power-reactive power, frequency-active power, etc


Structure
=========

The project structure is depicted in the diagram below. The primary function through which users interact with is the 'OpenDERInterface',
which enables users to connect with OpenDER, VR_Model, and power system simulators. In this project, the 'Simulationinterface' is an
abstract class, serving as an interface of power system simulators. This design allows for easy integration with various
simulators, with the simulators inheriting from class 'Simulationinterface'.

.. image:: interface.png
    :width: 1000
    :align: center





Installation
============
To install dependencies, two options are available:

1. Automatic Installation: Use the following command to automatically install the dependencies:

    ``pip install -e ./``

2. Manual Installation: Alternatively, you can manually install the dependencies by referring to the 'requirements.txt' file. This file contains a list of the required dependencies along with their specific versions. You can install them individually using standard pip commands


If you want have separate project - ***

Examples
=========
* volt-var: demonstrate plotting capabilities
* OpenDSS_34bus - dynamic simulation: interactions between voltage regulators and DER enter service performance
* OpenDSS_34bus - steady state simulation: comparison between OpenDSS internal inverter model vs OpenDER
* OpenDSS_GFOV - single_isource: dynamic simulation of isource experiencing a ground fault over voltage
* OpenDSS_GFOV - single_vsource: dynamic simulation of vsource experiencing a ground fault over voltage
* OpenDSS_BESS_PV: 15min time series simulation using BESS for PV power peak shaving


**Users are encouraged and expected to make changes to the released package for their usage.**
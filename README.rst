=================
OpenDER interface
=================

This project includes simulation interfaces for `OpenDER <https://github.com/epri-dev/opender/>`__ model, including:

* Connecting OpenDER to OpenDSS for circuit simulation
* Plot time series chart
* Plot steady-state charts, including voltage-reactive power, active power-reactive power, frequency-active power, etc

More features and documentations are in development.

**Users are encouraged and expected to make changes to the released package for their usage.**

To install the package:
=======================
Type the following command in the project directory

``pip install -e ./``

This will install all dependent packages.

If you want have separate project - ***

Examples:
=========
* volt-var: demonstrate plotting capabilities
* OpenDSS_34bus - dynamic simulation: interactions between voltage regulators and DER enter service performance
* OpenDSS_34bus - steady state simulation: comparison between OpenDSS internal inverter model vs OpenDER
* OpenDSS_GFOV: dynamic simulation of a ground fault over voltage
* OpenDSS_BESS_PV: 15min time series simulation using BESS for PV power peak shaving

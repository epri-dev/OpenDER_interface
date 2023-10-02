"""
Copyright © 2023 Electric Power Research Institute, Inc. All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:
· Redistributions of source code must retain the above copyright notice,
  this list of conditions and the following disclaimer.
· Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.
· Neither the name of the EPRI nor the names of its contributors may be used
  to endorse or promote products derived from this software without specific
  prior written permission.
"""

import pytest
import pathlib
import os
from opender import DER, DER_PV, DER_BESS, DERCommonFileFormat
from opender_interface import DERInterface,OpenDSSInterface
from conftest import showplt


class TestDERInterface:
    def test_der_interface(self):
        script_path = pathlib.Path(os.path.dirname(__file__))
        circuit_folder = script_path
        dss_file = circuit_folder.joinpath("test_circuit.dss")

        #Create DERInterface
        ckt_int = DERInterface(dss_file)
        ckt_int.cmd('New PVSystem.PV1 Bus1=der.1.2.3 Phases=3, kV=12.47 Pmpp=5000 kVA=5000 irradiance=1 kvarMax=2200.0 kvarMaxAbs=-2200.0 PFpriority=Yes pf=1 vminpu=0.1 irradiance = 1 %cutin=0.00001, %cutout=0.0000001')
        #initialize circuit
        ckt_int.initialize()

        # connect a DER to each bus and create DER model interface
        der_file = DERCommonFileFormat()

        der_list = ckt_int.create_opender_objs(der_files=der_file)

        assert len(der_list) == 1

        ckt = OpenDSSInterface(str(dss_file))
        ckt_int = DERInterface(ckt,print_der=False)
        ckt_int.cmd('New generator.PV1 Bus1=der.1.2.3 Phases=3, kV=12.47 kw=5000 kVA=5000 ')
        ckt_int.initialize(DER_sim_type='generator')

        # create voltage regulator controls objects to replace the ones in the circuit
        ckt_int.create_vr_objs()

        der_file = DERCommonFileFormat(NP_VA_MAX=4000000,
                                       NP_P_MAX=4000000,
                                       NP_Q_MAX_INJ=1760000,
                                       NP_Q_MAX_ABS=1760000)

        der_list = ckt_int.create_opender_objs(p_pu=0.9, der_files=der_file)

        assert len(der_list) == 1

        ckt_int.der_convergence_process()
        lines=ckt_int.read_line_flow()
        assert abs(lines['flowS_C'].loc['line1'].real - (5000-4000*0.9)/3) < 500

        buses=ckt_int.read_sys_voltage()

        assert abs(buses['Vpu_A'].loc['der']-1) < 0.05

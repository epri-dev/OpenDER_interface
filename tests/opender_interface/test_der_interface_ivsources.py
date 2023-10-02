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

        ckt = OpenDSSInterface(str(dss_file))
        ckt_int = DERInterface(ckt,print_der=False)
        ckt_int.cmd(['New isource.PV1_a Bus1=der.1 Phases=1',
                     'New isource.PV1_b Bus1=der.2 Phases=1',
                     'New isource.PV1_c Bus1=der.3 Phases=1'])
        ckt_int.initialize(DER_sim_type='isource')

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


        ckt = OpenDSSInterface(str(dss_file))
        ckt_int = DERInterface(ckt,print_der=False)
        ckt_int.cmd(['New vsource.PV1_a Bus1=der.1 Phases=1, basekV=12, baseMVA=0.1, pu=0.6, r1=0  x1=1  r0=0 x0=1 angle = 0',
                     'New vsource.PV1_b Bus1=der.2 Phases=1, basekV=12, baseMVA=0.1, pu=0.6, r1=0  x1=1  r0=0 x0=1 angle = 0',
                     'New vsource.PV1_c Bus1=der.3 Phases=1, basekV=12, baseMVA=0.1, pu=0.6, r1=0  x1=1  r0=0 x0=1 angle = 0'])


        ckt_int.initialize(DER_sim_type='vsource')

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
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
from opender import DER, DER_PV, DER_BESS
from opender_interface import XYPlots
from conftest import showplt

pu = [True, False]


class TestXYPlot:
    @pytest.mark.parametrize("pu", pu)
    def test_xy_plot(self, pu):
        der_obj = DER_PV()
        xyplot = XYPlots(der_obj, pu=pu)

        der_obj.update_der_input(p_dc_pu=0.8,v_pu=1,f=61)
        der_obj.run()

        xyplot.add_point_to_plot()
        xyplot.prepare_fp_plot(p_avl_list=[1],p_pre_list=[0.8])

        if showplt:
            xyplot.show()

        der_obj = DER_BESS()
        der_obj.der_file.NP_P_MAX_CHARGE = 80e3
        xyplot = XYPlots(der_obj, pu=pu)

        der_obj.update_der_input(p_dem_pu=-0.5,v_pu=1,f=61)
        der_obj.run()

        xyplot.add_point_to_plot()
        xyplot.prepare_fp_plot(p_avl_list=[1],p_pre_list=[-0.5])

        if showplt:
            xyplot.show()


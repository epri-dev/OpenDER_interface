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

        der_obj.der_file.QV_MODE_ENABLE = True

        der_obj.update_der_input(p_dc_pu=1,v_pu=1.09)
        der_obj.run()

        xyplot.add_point_to_plot()
        xyplot.prepare_vq_plot()

        if showplt:
            xyplot.show()



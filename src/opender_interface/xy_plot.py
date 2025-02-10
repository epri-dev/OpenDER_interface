# Copyright © 2023 Electric Power Research Institute, Inc. All rights reserved.

# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
# · Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
# · Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# · Neither the name of the EPRI nor the names of its contributors may be used
#   to endorse or promote products derived from this software without specific
#   prior written permission.


import sys
import os
import pathlib
import matplotlib.pyplot as plt
import numpy as np
import opender.der
import pandas as pd
import pickle
import matplotlib
import time
from copy import deepcopy

# set plot style
script_path = pathlib.Path(os.path.dirname(__file__))
plt.style.use(str(script_path)+'/xyplot.mplstyle')


class XYPlots:
    """
    This class generates steady state figures for OpenDER. Currently, it supports creating:
        - Voltage-reactive power for volt-var function
        - Voltage-active power for volt-watt function
        - Active power-reactive power for constant power factor or watt-var function, as well as demonstrating the power capability
        - Frequency-active power for frequency-droop function
        - Three phase voltage phasor for unbalanced voltage
    """

    def __init__(self, der_obj, pu=True):
        """
        The plots directly reads the rating and control setting information in the OpenDER object.

        :param der_obj: OpenDER object that the figure is based on.
        """

        self.der_obj = der_obj
        self.der_file = self.der_obj.der_file

        self._kva = self.der_obj.der_file.NP_VA_MAX / 1000
        self._kva_abs = self.der_file.NP_APPARENT_POWER_CHARGE_MAX / 1000
        self._kvar_inj = self.der_obj.der_file.NP_Q_MAX_INJ / 1000
        self._kvar_abs = self.der_obj.der_file.NP_Q_MAX_ABS / 1000
        self._p_max = self.der_obj.der_file.NP_P_MAX / 1000

        self.x_list = list()
        self.y_list = list()
        self.marker_list = list()
        self.markersize_list = list()
        self.color_list = list()

        self.plot_points_saved = []
        self.meas_points_dict = []
        self.plot_element = None

        self.plot_points = []
        self.meas_points = None
        self.fig_vp = None
        self.fig_v3 = None
        self.fig_pq = None
        self.fig_vq = None
        self.fig_fp = None

        self.ax_pq = None
        self.ax_vq = None
        self.ax_v3 = None
        self.ax_vp = None
        self.ax_fp = None

        self.qp_curve_fig_obj = None
        self.ap_limit_fig_obj = None
        self.const_pf_fig_obj = None

        self.pu = pu

    def save_fig(self, path: str):
        """
        Save prepared figures as svg files in given path. No file extension is needed. For example, if provided with
        'Figure':
            - Voltage-reactive power plot will be saved as 'Figure_vq.svg'
            - Voltage-active power plot will be saved as 'Figure_vp.svg'
            - Active power-reactive power plot will be saved as 'Figure_pq.svg'
            - Frequency-active power plot will be saved as 'Figure_fp.svg'
            - Three phase phasor pot will be saved as 'Figure_v3.svg'

        :param path: Path for the saved figures. No file extension.
        """
        if self.fig_pq is not None:
            self.fig_pq.savefig(path+'_pq.svg', format='svg', dpi=1200)
        if self.fig_vp is not None:
            self.fig_vp.savefig(path + '_vp.svg', format='svg', dpi=1200)
        if self.fig_vq is not None:
            self.fig_vq.savefig(path + '_vq.svg', format='svg', dpi=1200)
        if self.fig_v3 is not None:
            self.fig_v3.savefig(path + '_v3.svg', format='svg', dpi=1200)
        if self.fig_fp is not None:
            self.fig_fp.savefig(path + '_fp.svg', format='svg', dpi=1200)

    def set_title_labels(self, axes: plt.Axes, title: str, xlabel: str, ylabel: str):
        """
        Set figure title and label.

        :param axes: subplot (axes) object (matplotlib.pyplot)
        :param title: Subplot title
        :param xlabel: Subplot x-axis label
        :param ylabel: Subplot y-axis label
        """
        axes.set_title(title)
        axes.set_xlabel(xlabel)
        axes.set_ylabel(ylabel)

    def add_point_to_plot(self, der_obj: opender.DER = None) -> None:
        """
        Save current operating status information of the OpenDER object for future plotting.
        :param der_obj: If not provided, the OpenDER object provided in the initialization process will be used.
        """
        if der_obj is None:
            der_obj = self.der_obj

        self.plot_points.append(deepcopy(der_obj))

        '''
        {
            'p_out_pu': der_obj.p_out_pu,
            'q_out_pu': der_obj.q_out_pu,
            'p_desired_pu': der_obj.p_desired_pu,
            'q_desired_pu': der_obj.q_desired_pu,
            'CONST_PF_MODE_ENABLE': der_obj.exec_delay.const_pf_mode_enable_exec,
            'CONST_PF':der_obj.exec_delay.const_pf_exec,
            'CONST_PF_EXCITATION': der_obj.exec_delay.const_pf_excitation_exec,
            'v_meas_pu': der_obj.der_input.v_meas_pu,
            'freq_hz': der_obj.der_input.freq_hz
        }
        
        '''

    def add_measurement_to_plot(self, V: float = None, P: float = None, Q: float = None, F: float = None) -> None:
        """
        Save arbitrary DER operating status information for future plotting. Usually used for model validation purpose.
        :param V: DER RPA voltage in pu.
        :param P: DER output active power in pu.
        :param Q: DER output reactive power in pu.
        :param F: DER RPA frequency in Hertz
        """
        self.meas_points_dict.append({
            'V': V,
            'P': P,
            'Q': Q,
            'F': F,
        })

    def show(self) -> None:
        """
        show all plotted figures
        """
        plt.show()

    def __calc_S(self, value: float) -> float:
        """
        If self.pu is True, return pu value based on nameplate apparent power rating. If False, return kVAR value.

        :param value: reactive power in pu of nameplate apparent power rating
        """
        if self.pu:
            return value
        else:
            return value * self.der_file.NP_VA_MAX / 1000

    def __calc_P(self, value: float) -> float:
        """
        If self.pu is True, return pu value based on nameplate apparent power rating. If False, return kW value.

        :param value: active power in pu of nameplate active power rating, considering the difference of charging and discharging
        """
        if self.pu:
            return value * self.der_file.NP_P_MAX / self.der_file.NP_VA_MAX if value > 0 \
                else value * self.der_file.NP_P_MAX_CHARGE / self.der_file.NP_VA_MAX
        else:
            return value * self.der_file.NP_P_MAX / 1000 if value > 0 else value * self.der_file.NP_P_MAX_CHARGE / 1000

    def prepare_pq_plot(self):
        """
        Prepare plot with x-axis as P and y-axis as Q. Show apparent power circle, reactive power capability requirement
        as per IEEE 1547-2018 and reactive power capability of the modeled DER.
        If constant power factor mode is enabled, the constant power factor setting is plotted.
        If watt-var mode is enabled, its piecewise linear curve is also plotted.
        """

        # Initialize figure
        self.fig_pq, self.ax_pq = plt.subplots(nrows=1, ncols=1)
        self.ax_pq.set_title("PQ Plane")
        if self.pu:
            self.set_title_labels(self.ax_pq, 'PQ Plane', "Active Power (pu)", "Reactive Power (pu)")
        else:
            self.set_title_labels(self.ax_pq, 'PQ Plane', "Active Power (kW)", "Reactive Power (kvar)")

        # save all elements in plot for possible animation purpose.
        self.plot_element = []

        # Draw XY axis
        self.plot_element.append(self.ax_pq.plot([0, 0], [-self.__calc_S(1), self.__calc_S(1)], color='grey'))
        self.plot_element.append(self.ax_pq.plot([-self.__calc_S(1), self.__calc_S(1)], [0, 0], color='grey'))

        # Draw VA circle
        theta1 = np.linspace(-np.pi / 2, np.pi / 2, 100)
        theta2 = np.linspace(np.pi / 2, 3 * np.pi / 2, 100)
        if self.pu:
            x1 = np.cos(theta1)
            x2 = np.sin(theta1)
            x3 = self.der_file.NP_APPARENT_POWER_CHARGE_MAX/self.der_file.NP_VA_MAX * np.cos(theta2)
            x4 = self.der_file.NP_APPARENT_POWER_CHARGE_MAX/self.der_file.NP_VA_MAX * np.sin(theta2)
        else:
            x1 = self._kva * np.cos(theta1)
            x2 = self._kva * np.sin(theta1)
            x3 = self._kva_abs * np.cos(theta2)
            x4 = self._kva_abs * np.sin(theta2)
        self.plot_element.append(self.ax_pq.plot(x1, x2, color='red', label='S Rating'))
        self.plot_element.append(self.ax_pq.plot(x3, x4, color='red'))

        # Draw P max
        self.plot_element.append(self.ax_pq.plot([self.__calc_P(1), self.__calc_P(1)], [-self.__calc_S(1), self.__calc_S(1)], color='green', label="P Max"))
        if type(self.der_obj) is opender.DER_BESS:
            self.plot_element.append(self.ax_pq.plot([self.__calc_P(-1), self.__calc_P(-1)], [-self.__calc_S(1), self.__calc_S(1)], color='green'))

        # Draw Q requirements by IEEE 1547-2018
        self.plot_element.append(self.ax_pq.plot([self.__calc_P(0.2), self.__calc_S(1)],
                                                 [self.__calc_S(0.44), self.__calc_S(0.44)], color='pink', label="Q Cap Req (Cat_B)"))
        self.plot_element.append(self.ax_pq.plot([self.__calc_P(0.05), self.__calc_P(0.2)],
                                                 [self.__calc_S(0.11), self.__calc_S(0.44)], color='pink'))

        self.plot_element.append(self.ax_pq.plot([self.__calc_P(0.2), self.__calc_S(1)], [self.__calc_S(-0.44), self.__calc_S(-0.44)], color='pink'))
        self.plot_element.append(self.ax_pq.plot([self.__calc_P(0.05), self.__calc_P(0.2)], [self.__calc_S(-0.11), self.__calc_S(-0.44)], color='pink'))

        # Draw DER Q capability
        k=8
        # Q injection capability
        for i in range(len(self.der_obj.der_file.NP_Q_CAPABILITY_BY_P_CURVE['P_Q_INJ_PU']) - 1):
            k = k + 1
            self.plot_element.append(self.ax_pq.plot(
                [self.__calc_S(self.der_obj.der_file.NP_Q_CAPABILITY_BY_P_CURVE['P_Q_INJ_PU'][i]),
                 self.__calc_S(self.der_obj.der_file.NP_Q_CAPABILITY_BY_P_CURVE['P_Q_INJ_PU'][i + 1])],
                [self.__calc_S(self.der_obj.der_file.NP_Q_CAPABILITY_BY_P_CURVE['Q_MAX_INJ_PU'][i]),
                 self.__calc_S(self.der_obj.der_file.NP_Q_CAPABILITY_BY_P_CURVE['Q_MAX_INJ_PU'][i + 1])], color='black'))

        # Q absorption capability
        for i in range(len(self.der_obj.der_file.NP_Q_CAPABILITY_BY_P_CURVE['P_Q_ABS_PU']) - 1):
            k = k + 1
            self.plot_element.append(self.ax_pq.plot(
                [self.__calc_S(self.der_obj.der_file.NP_Q_CAPABILITY_BY_P_CURVE['P_Q_ABS_PU'][i]),
                 self.__calc_S(self.der_obj.der_file.NP_Q_CAPABILITY_BY_P_CURVE['P_Q_ABS_PU'][i + 1])],
                [self.__calc_S(-self.der_obj.der_file.NP_Q_CAPABILITY_BY_P_CURVE['Q_MAX_ABS_PU'][i]),
                 self.__calc_S(-self.der_obj.der_file.NP_Q_CAPABILITY_BY_P_CURVE['Q_MAX_ABS_PU'][i + 1])], color='blue'))

        k=k+2
        self.plot_element.append(self.ax_pq.plot([0, 0], [0, 0], color='black', label="Q Inj Max"))
        self.plot_element.append(self.ax_pq.plot([0, 0], [0, 0], color='blue', label="Q Abs Max"))

        # Draw DER operation status (P and Q)
        self.meas_points = pd.DataFrame(self.meas_points_dict)

        for der_obj in self.plot_points:
            self.ax_pq.scatter(self.__calc_S(der_obj.p_out_pu),self.__calc_S(der_obj.q_out_pu), s=90, marker='^', color='blue')
        for i, point in self.meas_points.iterrows():
            self.ax_pq.scatter(self.__calc_S(self.meas_points['P'].values[i]), self.__calc_S(self.meas_points['Q'].values[i]),
                               marker='v', s=90, color='orange')

        # Draw constant power factor line
        if self.der_obj.der_file.CONST_PF_MODE_ENABLE:
            pf = self.der_obj.der_file.CONST_PF
            if self.der_obj.der_file.CONST_PF_EXCITATION == "INJ":
                sign = 1
            else:
                sign = -1

            p = self.__calc_S(pf)
            q = self.__calc_S(sign * np.sqrt(1 - pf ** 2))

            if type(self.der_obj) is opender.DER_BESS:
                self.const_pf_fig_obj, = self.ax_pq.plot([-p, p], [-q, q], color='yellow', label=f"{pf} Power Factor")
            else:
                self.const_pf_fig_obj, = self.ax_pq.plot([0, p], [0, q], color='yellow', label=f"{pf} Power Factor")
        else:
            self.const_pf_fig_obj,  = self.ax_pq.plot([], [], color='yellow')

        # Draw watt-var lines
        if self.der_obj.der_file.QP_MODE_ENABLE:
            p1 = self.__calc_P(self.der_obj.der_file.QP_CURVE_P1_GEN)
            p2 = self.__calc_P(self.der_obj.der_file.QP_CURVE_P2_GEN)
            p3 = self.__calc_P(self.der_obj.der_file.QP_CURVE_P3_GEN)
            q1 = self.__calc_S(self.der_obj.der_file.QP_CURVE_Q1_GEN)
            q2 = self.__calc_S(self.der_obj.der_file.QP_CURVE_Q2_GEN)
            q3 = self.__calc_S(self.der_obj.der_file.QP_CURVE_Q3_GEN)
            p_1 = self.__calc_P(self.der_obj.der_file.QP_CURVE_P1_LOAD)
            p_2 = self.__calc_P(self.der_obj.der_file.QP_CURVE_P2_LOAD)
            p_3 = self.__calc_P(self.der_obj.der_file.QP_CURVE_P3_LOAD)
            q_1 = self.__calc_S(self.der_obj.der_file.QP_CURVE_Q1_LOAD)
            q_2 = self.__calc_S(self.der_obj.der_file.QP_CURVE_Q2_LOAD)
            q_3 = self.__calc_S(self.der_obj.der_file.QP_CURVE_Q3_LOAD)
            max = self.__calc_S(1)

            if type(self.der_obj) is opender.DER_BESS:
                self.qp_curve_fig_obj, = self.ax_pq.plot([-max, p_3, p_2, p_1, p1, p2, p3, max], [q_3, q_3, q_2, q_1, q1, q2, q3, q3], color='orange', label='Watt-var')
            else:
                self.qp_curve_fig_obj, = self.ax_pq.plot([0, p1, p2, p3, max], [q1, q1, q2, q3, q3], color='orange', linewidth=2, label='Watt-var')

        else:
            self.qp_curve_fig_obj, = self.ax_pq.plot([], [], color='yellow', label='')

        # Draw active power limit line
        if self.der_obj.der_file.AP_LIMIT_ENABLE:
            p = self.__calc_P(self.der_obj.der_file.AP_LIMIT)
            self.ap_limit_fig_obj, = self.ax_pq.plot([p,p], [-self.__calc_S(1), self.__calc_S(1)], color='brown', label='P limit')
        else:
            self.ap_limit_fig_obj, = self.ax_pq.plot([], [], color='brown', label='')

        self.ax_pq.set_aspect(1)

        if type(self.der_obj) is opender.DER_BESS:
            self.ax_pq.legend(loc=1)
        else:
            self.ax_pq.legend(loc=2)

    def prepare_vq_plot(self):
        """
        Prepare plot with x-axis as V and y-axis as Q. Volt-var curve is also plotted based on modeled OpenDER setting
        """
        self.fig_vq, self.ax_vq = plt.subplots(nrows=1, ncols=1)
        v_curve = np.array([0.85, self.der_file.QV_CURVE_V1, self.der_file.QV_CURVE_V2, self.der_file.QV_CURVE_V3,
                            self.der_file.QV_CURVE_V4, 1.15])
        q_curve = np.array(
            [self.der_file.QV_CURVE_Q1, self.der_file.QV_CURVE_Q1, self.der_file.QV_CURVE_Q2, self.der_file.QV_CURVE_Q3,
             self.der_file.QV_CURVE_Q4, self.der_file.QV_CURVE_Q4])

        q_curve = [self.__calc_S(q) for q in q_curve]
        self.ax_vq.plot(v_curve, q_curve, color='red', label='Volt-Var Curve')

        for der_obj in self.plot_points:
            self.ax_vq.scatter(der_obj.der_input.v_meas_pu, self.__calc_S(der_obj.q_out_pu), marker='^', s=90, color='blue')

        if self.meas_points_dict != []:
            self.meas_points = pd.DataFrame(self.meas_points_dict)
        else:
            self.meas_points = pd.DataFrame()

        for i, point in self.meas_points.iterrows():
            self.ax_vq.scatter(self.meas_points['V'].values[i], self.__calc_S(self.meas_points['Q'].values[i]),
                               marker='v', s=90, color='orange')

        if self.pu:
            self.set_title_labels(self.ax_vq, 'Volt-var', "Voltage (pu)", "Reactive Power (pu)")
        else:
            self.set_title_labels(self.ax_vq, 'Volt-var', "Voltage (pu)", "Reactive Power (kvar)")

        self.ax_vq.legend(loc=1)

    def prepare_vp_plot(self):
        """
        Prepare plot with x-axis as V and y-axis as P. Volt-watt curve is also plotted based on modeled OpenDER setting
        """
        self.fig_vp, self.ax_vp = plt.subplots(nrows=1, ncols=1)

        v_curve = np.array([0.98, self.der_file.PV_CURVE_V1, self.der_file.PV_CURVE_V2, 1.12])

        p_curve = np.array(
            [self.__calc_P(self.der_file.PV_CURVE_P1),
             self.__calc_P(self.der_file.PV_CURVE_P1),
             self.__calc_P(self.der_file.PV_CURVE_P2),
             self.__calc_P(self.der_file.PV_CURVE_P2)])
        self.ax_vp.plot(v_curve, p_curve, color='red', label='Volt-Watt Curve')

        if self.meas_points_dict != []:
            self.meas_points = pd.DataFrame(self.meas_points_dict)
        else:
            self.meas_points = pd.DataFrame()

        for der_obj in self.plot_points:
            self.ax_vp.scatter(der_obj.der_input.v_meas_pu, self.__calc_S(der_obj.p_out_pu), marker='^', s=90, color='blue')
        for i, point in self.meas_points.iterrows():
            self.ax_vp.scatter(self.meas_points['V'].values[i], self.__calc_S(self.meas_points['P'].values[i]),
                               marker='v', s=90, color='orange')

        if self.der_obj.der_file.AP_LIMIT_ENABLE:
            p = self.__calc_P(self.der_obj.der_file.AP_LIMIT)
            self.ap_limit_fig_obj, = self.ax_vp.plot([0.98,1.12], [p, p], color='brown', label='P limit')
        else:
            self.ap_limit_fig_obj, = self.ax_vp.plot([], [], color='brown', label='')

        if type(self.der_obj) is opender.DER_BESS:
            self.ax_vp.plot([0.9, 1.15], [0, 0], color = 'black')

        self.ax_vp.legend(loc=1)
        self.ax_vp.set_xlim([0.97, 1.13])

        if self.pu:
            self.set_title_labels(self.ax_vp, 'Volt-watt', "Voltage (pu)", "Active Power (pu)")
        else:
            self.set_title_labels(self.ax_vp, 'Volt-watt', "Voltage (pu)", "Active Power (kW)")

    def prepare_v3_plot(self, l2l=False, v_vector=None):
        """
        Prepare three-phase voltage phasor chart based on modeled OpenDER object's RPA voltage.
        ALso accept arbitrary coordinates provided in parameter v_vector. The format is
        [V_a_mag, V_b_mag, V_c_mag, Theta_a, Theta_b, Theta_c]. Unit of Theta is radian.

        :param l2l: Print line-to-line voltage phasors
        :param v_vector: Print arbitrary phasor coordinates. If not provided, the OpenDER object's RPA voltage is used
        """
        self.fig_v3, self.ax_v3 = plt.subplots(nrows=1, ncols=1)

        # Calculate coordinates with
        import math
        if v_vector is None:
            x_a = self.der_obj.der_input.v_a * math.cos(self.der_obj.der_input.theta_a) / self.der_file.NP_AC_V_NOM
            y_a = self.der_obj.der_input.v_a * math.sin(self.der_obj.der_input.theta_a) / self.der_file.NP_AC_V_NOM
            x_b = self.der_obj.der_input.v_b * math.cos(self.der_obj.der_input.theta_b) / self.der_file.NP_AC_V_NOM
            y_b = self.der_obj.der_input.v_b * math.sin(self.der_obj.der_input.theta_b) / self.der_file.NP_AC_V_NOM
            x_c = self.der_obj.der_input.v_c * math.cos(self.der_obj.der_input.theta_c) / self.der_file.NP_AC_V_NOM
            y_c = self.der_obj.der_input.v_c * math.sin(self.der_obj.der_input.theta_c) / self.der_file.NP_AC_V_NOM
        else:
            x_a = v_vector[0] * math.cos(v_vector[3])
            x_b = v_vector[1] * math.cos(v_vector[4])
            x_c = v_vector[2] * math.cos(v_vector[5])
            y_a = v_vector[0] * math.sin(v_vector[3])
            y_b = v_vector[1] * math.sin(v_vector[4])
            y_c = v_vector[2] * math.sin(v_vector[5])

        ## Another type of arrow
        # from matplotlib.patches import FancyArrowPatch
        # arrow_a = FancyArrowPatch((0, 0), (x_a, y_a), mutation_scale=30)
        # arrow_b = FancyArrowPatch((0, 0), (x_b, y_b), mutation_scale=30)
        # arrow_c = FancyArrowPatch((0, 0), (x_c, y_c), mutation_scale=30)
        # self.ax.add_patch(arrow_a)
        # self.ax.add_patch(arrow_b)
        # self.ax.add_patch(arrow_c)

        prop = dict()
        # dict(arrowstyle="-|>,head_width=2,head_length=5",
        #      shrinkA=0, shrinkB=0)

        if l2l:
            plt.annotate("", xy=(x_a, y_a), xytext=(x_b, y_b), arrowprops=prop)
            plt.annotate("", xy=(x_b, y_b), xytext=(x_c, y_c), arrowprops=prop)
            plt.annotate("", xy=(x_c, y_c), xytext=(x_a, y_a), arrowprops=prop)

        plt.annotate("", xy=(x_a, y_a), xytext=(0, 0), arrowprops=dict(color='brown')) # arrowstyle = "->",
        plt.annotate("", xy=(x_b, y_b), xytext=(0, 0), arrowprops=dict(color='orange'))
        plt.annotate("", xy=(x_c, y_c), xytext=(0, 0), arrowprops=dict(color='gold'))

        # Hide grid lines
        self.ax_v3.grid(False)

        # Hide axes ticks
        self.ax_v3.set_xticks([])
        self.ax_v3.set_yticks([])

        self.ax_v3.set_xlim(-max(x_a, x_b, x_c, y_a, y_b, y_c)*2, max(x_a, x_b, x_c, y_a, y_b, y_c)*2)
        self.ax_v3.set_ylim(-max(x_a, x_b, x_c,y_a, y_b, y_c)*2, max(x_a, x_b, x_c, y_a, y_b, y_c)*2)
        plt.axis('equal')

    def prepare_fp_plot(self, p_pre_list, p_avl_list=None):
        """
        Prepare plot with x-axis as F and y-axis as P. Frequency-droop curve is also plotted based on modeled OpenDER
        setting and provided pre-disturbance active power and available active power.

        :param p_pre_list: List of pre-disturbance active power P_pre values for plotting frequency-droop curve
        :param p_avl_list: List of available active power P_avl values for plotting frequency-droop curve
        """

        self.fig_fp, self.ax_fp = plt.subplots(nrows=1, ncols=1)

        colors = ['red', 'blue', 'purple', 'orange']

        # Plot frequency-droop curves
        for i, p_pre in enumerate(p_pre_list):
            if p_avl_list is None:
                p_avl = 1
            else:
                p_avl = p_avl_list[i]

            f1 = self.der_file.UF2_TRIP_F
            if (60 - self.der_file.PF_DBUF - f1)/self.der_file.PF_KUF/60 + p_pre >= p_avl:
                p1 = p_avl
                p2 = p_avl
                f2 = (p_pre - p_avl) * self.der_file.PF_KUF * 60 + 60 - self.der_file.PF_DBUF
            else:
                f2 = f1
                p1 = p2 = (60 - self.der_file.PF_DBUF - f1)/self.der_file.PF_KUF/60 + p_pre

            f4 = self.der_file.OF2_TRIP_F

            if self.der_file.NP_P_MIN_PU < 0:
                NP_P_MIN_PU_eff = self.der_file.NP_P_MIN_PU * self.der_file.NP_P_MAX_CHARGE / self.der_file.NP_P_MAX
            else:
                NP_P_MIN_PU_eff = self.der_file.NP_P_MIN_PU

            if -(f4 - 60 - self.der_file.PF_DBOF)/self.der_file.PF_KOF/60 + p_pre <= NP_P_MIN_PU_eff:
                p4 = NP_P_MIN_PU_eff
                p3 = NP_P_MIN_PU_eff
                f3 = (p_pre- NP_P_MIN_PU_eff) * self.der_file.PF_KOF*60 + 60 + self.der_file.PF_DBOF
            else:
                f3 = f4
                p4 = p3 = -(f4 - 60 - self.der_file.PF_DBOF)/self.der_file.PF_KOF/60 + p_pre

            f_curve = [f1, f2, 60-self.der_file.PF_DBUF, 60, 60+self.der_file.PF_DBOF, f3, f4]

            p_curve = [self.__calc_S(p) for p in[p1, p2, p_pre, p_pre, p_pre, p3, p4]]

            self.ax_fp.plot(f_curve, p_curve)

        # Plot abnormal frequency trip settings
        self.ax_fp.plot([self.der_file.UF2_TRIP_F, self.der_file.UF2_TRIP_F], [self.__calc_S(-1.1), self.__calc_S(1.1)], color='gray', linestyle='--')
        self.ax_fp.plot([self.der_file.OF2_TRIP_F, self.der_file.OF2_TRIP_F], [self.__calc_S(-1.1), self.__calc_S(1.1)], color='gray', linestyle='--')
        self.ax_fp.plot([self.der_file.UF1_TRIP_F, self.der_file.UF1_TRIP_F], [self.__calc_S(-1.1), self.__calc_S(1.1)], color='gray', linestyle='-.')
        self.ax_fp.plot([self.der_file.OF1_TRIP_F, self.der_file.OF1_TRIP_F], [self.__calc_S(-1.1), self.__calc_S(1.1)], color='gray', linestyle='-.')

        # Plot OpenDER outputs
        for der_obj in self.plot_points:
            self.ax_fp.scatter(der_obj.der_input.freq_hz, self.__calc_S(der_obj.p_out_pu), marker='^', s=90, color='blue')

        # Plot measured points
        if self.meas_points_dict != []:
            self.meas_points = pd.DataFrame(self.meas_points_dict)
        else:
            self.meas_points = pd.DataFrame()

        for i, point in self.meas_points.iterrows():
            self.ax_fp.scatter(self.meas_points['F'].values[i], self.__calc_S(self.meas_points['P'].values[i]),
                               marker='v', s=90, color='orange')

        self.ax_fp.legend(loc=1)
        # self.ax_fp.set_ylim(0, 1.05)
        if self.pu:
            self.set_title_labels(self.ax_fp, 'Freq-droop', "Frequency (Hz)", "Active Power (pu)")
        else:
            self.set_title_labels(self.ax_fp, 'Freq-droop', "Frequency (Hz)", "Active Power (kW)")

    ######################################################################################################
    ### Unpolished code for making animations
    ######################################################################################################
    # def prepare_ani(self):
    #     print_der('preparing animations')
    #
    #     from matplotlib.animation import FuncAnimation
    #
    #     matplotlib.rcParams['animation.ffmpeg_path'] = r'C:\xxxxxxxx\ffmpeg.exe' # Please install ffmpeg and reference it here.
    #
    #     self.point = self.ax_pq.scatter(0, 0, s=90, color='blue')
    #     self.point_hollow = self.ax_pq.scatter(0, 0, s=80, facecolors='none', edgecolors='green')
    #
    #     self.ani = FuncAnimation(self.fig_pq, self.animate, interval=100, blit=True,
    #                              save_count=int(len(self.plot_points) * 1.1))
    #
    # def animate(self, i):
    #     self.point.remove()  # update the Data
    #
    #     if i>=len(self.plot_points):
    #         i=len(self.plot_points)-1
    #
    #     self.point = self.ax_pq.scatter(self.plot_points[i].p_out_kw, self.plot_points[i].q_out_kvar, s=90, color='blue')
    #
    #     self.point_hollow.remove()
    #     self.point_hollow = self.ax_pq.scatter(self.__calc_P(self.plot_points[i].p_desired_pu),
    #                                            self.__calc_S(self.plot_points[i].q_desired_pu), s=80,
    #                                            facecolors='none', edgecolors='green')
    #     # print_der(self.const_pf_fig_obj)
    #     v = self.plot_points[i].der_input.v_meas_pu
    #     self.time_text.set_text(f't={(i-2)*opender.der.DER.t_s:.1f}\r\nv_pu={v:.1f}')
    #
    #     if self.plot_points[i].der_file.CONST_PF_MODE_ENABLE:
    #         pf=self.plot_points[i].der_file.CONST_PF
    #
    #         if self.plot_points[i].der_file.CONST_PF_EXCITATION == "INJ":
    #             sign = 1
    #         else:
    #             sign = -1
    #
    #         p = self._kva * pf
    #         q = sign * self._kva * np.sqrt(1 - pf ** 2)
    #         self.const_pf_fig_obj.remove()
    #         self.const_pf_fig_obj, = self.ax_pq.plot([0, p], [0, q], color='yellow', label=f"{pf} Power Factor")
    #     else:
    #         self.const_pf_fig_obj.remove()
    #         self.const_pf_fig_obj, = self.ax_pq.plot([], [], color='yellow')
    #
    #     return self.point, self.point_hollow, self.time_text,self.const_pf_fig_obj
    #
    # def save_ani(self,path='fig.mp4'):
    #     print_der(f'Saving animations to {path}', end=' ')
    #     start = time.perf_counter()
    #     self.ani.save(path, fps=25, extra_args=['-vcodec', 'libx264'])
    #     print_der(f"... Completed in {time.perf_counter()-start:.1f}s")


import sys

import matplotlib.pyplot as plt
import numpy as np
import opender.der
import pandas as pd
import pickle
from matplotlib.animation import FuncAnimation
import matplotlib
import time

matplotlib.rcParams['animation.ffmpeg_path'] = r'C:\Users\pyma001\Box\_Documents\ffmpeg.exe'

mpl_dict = {'figure.facecolor': 'white',
 'axes.labelcolor': '.15',
 'xtick.direction': 'out',
 'ytick.direction': 'out',
 'xtick.color': '.15',
 'ytick.color': '.15',
 'axes.axisbelow': True,
 'grid.linestyle': '--',
 'text.color': '.15',
 'font.family': ['sans-serif'],
 'font.sans-serif': ['Arial', 'DejaVu Sans', 'Liberation Sans', 'Bitstream Vera Sans', 'sans-serif'],
 'lines.solid_capstyle': 'round',
 'patch.edgecolor': 'w',
 'patch.force_edgecolor': True,
 # 'image.cmap': 'rocket',
 'xtick.top': False,
 'ytick.right': False,
 'axes.grid': True,
 'axes.facecolor': 'white',
 'axes.edgecolor': '.8',
 'grid.color': '.8',
 'axes.spines.left': True,
 'axes.spines.bottom': True,
 'axes.spines.right': True,
 'axes.spines.top': True,
 'xtick.bottom': False,
 'ytick.left': False}

for key, value in mpl_dict.items():
    matplotlib.rcParams[key] = value



class XYPlots:
    def __init__(self, der_obj):
        self.der_obj = der_obj

        self.der_file = self.der_obj.der_file



        self._kva = self.der_obj.der_file.NP_VA_MAX
        self._kvar_inj = self.der_obj.der_file.NP_Q_MAX_INJ
        self._kvar_abs = self.der_obj.der_file.NP_Q_MAX_ABS
        self._p_max = self.der_obj.der_file.NP_P_MAX

        self.x_list = list()
        self.y_list = list()
        self.marker_list = list()
        self.markersize_list = list()
        self.color_list = list()

        self.plot_points_dict = []
        self.meas_points_dict = []

        self.plot_points = None
        self.fig_vp = None
        self.fig_v3 = None
        self.fig_pq = None
        self.fig_vq = None
        self.fig_pf = None

    def save_fig(self, path):
        if self.fig_pq is not None:
            self.fig_pq.savefig(path+'_pq.svg', format='svg', dpi=1200)
        if self.fig_vp is not None:
            self.fig_vp.savefig(path + '_vp.svg', format='svg', dpi=1200)
        if self.fig_vq is not None:
            self.fig_vq.savefig(path + '_vq.svg', format='svg', dpi=1200)
        if self.fig_v3 is not None:
            self.fig_v3.savefig(path + '_v3.svg', format='svg', dpi=1200)
        if self.fig_pf is not None:
            self.fig_pf.savefig(path + '_pf.svg', format='svg', dpi=1200)

    def set_title_labels(self, axes, title, xlabel, ylabel):
        axes.set_title(title)
        axes.set_xlabel(xlabel)
        axes.set_ylabel(ylabel)

    def add_point_to_plot(self, der_obj=None):
        if der_obj is None:
            der_obj = self.der_obj
        self.plot_points_dict.append({
            'p_out_pu': der_obj.p_out_pu,
            'q_out_pu': der_obj.q_out_pu,
            'p_desired_pu': der_obj.p_desired_pu,
            'q_desired_pu': der_obj.q_desired_pu,
            'CONST_PF_MODE_ENABLE': der_obj.exec_delay.const_pf_mode_enable_exec,
            'CONST_PF':der_obj.exec_delay.const_pf_exec,
            'CONST_PF_EXCITATION': der_obj.exec_delay.const_pf_excitation_exec,
            'v_meas_pu': der_obj.der_input.v_meas_pu,
            'freq_hz': der_obj.der_input.freq_hz
        })

    def add_measurement_to_plot(self, V=None, P=None, Q=None, F=None):
        self.meas_points_dict.append({
            'V':V,
            'P':P,
            'Q':Q,
            'F':F,
        })

    def prepare_ani(self):
        print('preparing animations')

        self.plot_points = pd.DataFrame(self.plot_points_dict)
        self.point = self.ax.scatter(0, 0, s=60, color='blue')
        self.point_hollow = self.ax.scatter(0, 0, s=80,
                                            facecolors='none', edgecolors='green')

        self.ani = FuncAnimation(self.fig, self.animate, interval=100, blit=True,save_count=int(len(self.plot_points)*1.1))


    def show(self):
        plt.show()

    def save_ani(self,path='fig.mp4'):
        print(f'Saving animations to {path}', end=' ')
        start = time.perf_counter()
        self.ani.save(path, fps=25, extra_args=['-vcodec', 'libx264'])
        print(f"... Completed in {time.perf_counter()-start:.1f}s")


    def calc_kvar(self, value):
        return value * self.der_file.NP_VA_MAX / 1000

    def calc_kw(self, value):
        return value * self.der_file.NP_P_MAX / 1000 if value > 0 else value * self.der_file.NP_P_MAX_CHARGE / 1000





    def prepare_pq_plot(self, pu=True):

        self.fig_pq, self.ax_pq = plt.subplots(nrows=1, ncols=1)
        self.ax_pq.set_title("PQ Plane")
        if pu:
            self.ax_pq.set_xlabel("Active Power (pu)")
            self.ax_pq.set_ylabel("Reactive Power (pu)")
        else:
            self.ax_pq.set_xlabel("Active Power (kW)")
            self.ax_pq.set_ylabel("Reactive Power (kvar)")
        self.plot_element=[]
        self.ax_pq.legend(loc=2)


        theta1 = np.linspace(-np.pi / 2, np.pi / 2, 100)
        theta2 = np.linspace(np.pi / 2, 3 * np.pi / 2, 100)

        if pu:
            x1 = np.cos(theta1)
            x2 = np.sin(theta1)
            x3 = self.der_file.NP_APPARENT_POWER_CHARGE_MAX/self.der_file.NP_VA_MAX * np.cos(theta2)
            x4 = self.der_file.NP_APPARENT_POWER_CHARGE_MAX/self.der_file.NP_VA_MAX * np.sin(theta2)
            self.plot_element.append(self.ax_pq.plot([0, 0], [-1,1], color='grey'))
            self.plot_element.append(self.ax_pq.plot([-1, 1], [0, 0], color='grey'))
        else:
            x1 = self._kva * np.cos(theta1)
            x2 = self._kva * np.sin(theta1)
            x3 = self.der_file.NP_APPARENT_POWER_CHARGE_MAX * np.cos(theta2)
            x4 = self.der_file.NP_APPARENT_POWER_CHARGE_MAX * np.sin(theta2)

            self.plot_element.append(self.ax_pq.plot([0, 0], [-self._kva, self._kva], color='grey'))
            self.plot_element.append(self.ax_pq.plot([-self._kva, self._kva], [0, 0], color='grey'))

        # P max
        if pu:
            self.plot_element.append(self.ax_pq.plot([self._p_max/self._kva, self._p_max/self._kva], [-1, 1], color='green', label="P Max"))
            if type(self.der_obj) is opender.DER_BESS:
                self.ax_pq.plot([-self.der_obj.der_file.NP_P_MAX_CHARGE/self._kva, -self.der_obj.der_file.NP_P_MAX_CHARGE/self._kva], [-1, 1], color='green')

        else:
            self.plot_element.append(self.ax_pq.plot([self._p_max, self._p_max], [-self._kva, self._kva], color='green', label="P Max"))
            if type(self.der_obj) is opender.DER_BESS:
                self.ax_pq.plot([-self.der_obj.der_file.NP_P_MAX_CHARGE, -self.der_obj.der_file.NP_P_MAX_CHARGE], [-self._kva, self._kva], color='green')

        # Q req
        if pu:
            self.plot_element.append(self.ax_pq.plot([self.der_obj.der_file.NP_P_MAX/self._kva * 0.2, 1],
                                                     [0.44, 0.44], color='pink',
                                                     label="Q Cap Req (Cat_B)"))
            self.plot_element.append(
                self.ax_pq.plot([self.der_obj.der_file.NP_P_MAX/self._kva * 0.05, self.der_obj.der_file.NP_P_MAX/self._kva * 0.2],
                                [0.11, 0.44], color='pink'))

            self.plot_element.append(self.ax_pq.plot([self.der_obj.der_file.NP_P_MAX/self._kva * 0.2, 1], [-0.44, -0.44], color='pink'))
            self.plot_element.append(self.ax_pq.plot([self.der_obj.der_file.NP_P_MAX/self._kva * 0.05, self.der_obj.der_file.NP_P_MAX/self._kva * 0.2], [-0.11, -0.44], color='pink'))

        else:
            self.plot_element.append(self.ax_pq.plot([self.der_obj.der_file.NP_P_MAX * 0.2, self._kva], [self.der_obj.der_file.NP_VA_MAX * 0.44, self.der_obj.der_file.NP_VA_MAX * 0.44], color='pink', label="Q Cap Req (Cat_B)"))
            self.plot_element.append(self.ax_pq.plot([self.der_obj.der_file.NP_P_MAX * 0.05, self.der_obj.der_file.NP_P_MAX * 0.2], [self.der_obj.der_file.NP_VA_MAX * 0.11, self.der_obj.der_file.NP_VA_MAX * 0.44], color='pink'))

            self.plot_element.append(self.ax_pq.plot([self.der_obj.der_file.NP_P_MAX * 0.2, self._kva], [-self.der_obj.der_file.NP_VA_MAX * 0.44, -self.der_obj.der_file.NP_VA_MAX * 0.44], color='pink'))
            self.plot_element.append(self.ax_pq.plot([self.der_obj.der_file.NP_P_MAX * 0.05, self.der_obj.der_file.NP_P_MAX * 0.2], [-self.der_obj.der_file.NP_VA_MAX * 0.11, -self.der_obj.der_file.NP_VA_MAX * 0.44], color='pink'))

        # kVA rating
        self.plot_element.append(self.ax_pq.plot(x1, x2, color='red', label='S Rating'))
        self.plot_element.append(self.ax_pq.plot(x3, x4, color='red'))


        # Q inj capability
        k=8
        if pu:
            for i in range(len(self.der_obj.der_file.NP_Q_CAPABILITY_BY_P_CURVE['P_Q_INJ_PU']) - 1):
                k = k + 1
                self.plot_element.append(self.ax_pq.plot(
                    [self.der_obj.der_file.NP_Q_CAPABILITY_BY_P_CURVE['P_Q_INJ_PU'][i] * self.der_obj.der_file.NP_P_MAX / self._kva,
                     self.der_obj.der_file.NP_Q_CAPABILITY_BY_P_CURVE['P_Q_INJ_PU'][
                         i + 1] * self.der_obj.der_file.NP_P_MAX / self._kva],
                    [self.der_obj.der_file.NP_Q_CAPABILITY_BY_P_CURVE['Q_MAX_INJ_PU'][
                         i],
                     self.der_obj.der_file.NP_Q_CAPABILITY_BY_P_CURVE['Q_MAX_INJ_PU'][
                         i + 1]], color='black'))

            # self.axes.plot([0.2 * self.der_file.NP_P_MAX, self._kva], [self._kvar_inj, self._kvar_inj], color='black', label="kvar Inj Max")
            # self.axes.plot([0.05 * self.der_file.NP_P_MAX, 0.2 * self.der_file.NP_P_MAX], [0.11 * self._kva, self._kvar_inj], color='black')

            # Q abs capability
            for i in range(len(self.der_obj.der_file.NP_Q_CAPABILITY_BY_P_CURVE['P_Q_ABS_PU']) - 1):
                k = k + 1
                self.plot_element.append(self.ax_pq.plot(
                    [self.der_obj.der_file.NP_Q_CAPABILITY_BY_P_CURVE['P_Q_ABS_PU'][i] * self.der_obj.der_file.NP_P_MAX/ self._kva,
                     self.der_obj.der_file.NP_Q_CAPABILITY_BY_P_CURVE['P_Q_ABS_PU'][
                         i + 1] * self.der_obj.der_file.NP_P_MAX/self._kva],
                    [-self.der_obj.der_file.NP_Q_CAPABILITY_BY_P_CURVE['Q_MAX_ABS_PU'][
                        i],
                     -self.der_obj.der_file.NP_Q_CAPABILITY_BY_P_CURVE['Q_MAX_ABS_PU'][
                         i + 1]], color='blue'))
        else:
            for i in range(len(self.der_obj.der_file.NP_Q_CAPABILITY_BY_P_CURVE['P_Q_INJ_PU'])-1):
                k=k+1
                self.plot_element.append(self.ax_pq.plot([self.der_obj.der_file.NP_Q_CAPABILITY_BY_P_CURVE['P_Q_INJ_PU'][i] * self.der_obj.der_file.NP_P_MAX, self.der_obj.der_file.NP_Q_CAPABILITY_BY_P_CURVE['P_Q_INJ_PU'][i + 1] * self.der_obj.der_file.NP_P_MAX],
                             [self.der_obj.der_file.NP_Q_CAPABILITY_BY_P_CURVE['Q_MAX_INJ_PU'][i]*self.der_obj.der_file.NP_VA_MAX, self.der_obj.der_file.NP_Q_CAPABILITY_BY_P_CURVE['Q_MAX_INJ_PU'][i+1]*self.der_obj.der_file.NP_VA_MAX], color='black'))


            # self.axes.plot([0.2 * self.der_file.NP_P_MAX, self._kva], [self._kvar_inj, self._kvar_inj], color='black', label="kvar Inj Max")
            # self.axes.plot([0.05 * self.der_file.NP_P_MAX, 0.2 * self.der_file.NP_P_MAX], [0.11 * self._kva, self._kvar_inj], color='black')

            # Q abs capability
            for i in range(len(self.der_obj.der_file.NP_Q_CAPABILITY_BY_P_CURVE['P_Q_ABS_PU'])-1):
                k=k+1
                self.plot_element.append(self.ax_pq.plot([self.der_obj.der_file.NP_Q_CAPABILITY_BY_P_CURVE['P_Q_ABS_PU'][i] * self.der_obj.der_file.NP_P_MAX, self.der_obj.der_file.NP_Q_CAPABILITY_BY_P_CURVE['P_Q_ABS_PU'][i + 1] * self.der_obj.der_file.NP_P_MAX],
                             [-self.der_obj.der_file.NP_Q_CAPABILITY_BY_P_CURVE['Q_MAX_ABS_PU'][i]*self.der_obj.der_file.NP_VA_MAX, -self.der_obj.der_file.NP_Q_CAPABILITY_BY_P_CURVE['Q_MAX_ABS_PU'][i+1]*self.der_obj.der_file.NP_VA_MAX], color='blue'))
        k=k+2
        self.plot_element.append(self.ax_pq.plot([0, 0], [0, 0], color='black', label="Q Inj Max"))
        self.plot_element.append(self.ax_pq.plot([0, 0], [0, 0], color='blue', label="Q Abs Max"))

        # self.axes.plot([0.2 * self.der_file.NP_P_MAX, self._kva], [-self._kvar_abs, -self._kvar_abs], color='blue', label="kvar Abs Max")
        # self.axes.plot([0.05 * self.der_file.NP_P_MAX, 0.2 * self.der_file.NP_P_MAX], [-0.11 * self._kva, -self._kvar_abs], color='blue')

        self.ax_pq.set_aspect(1)



        self.ax_pq.legend(loc=2)

        # self.time_text = plt.text(-self.der_obj.der_file.NP_P_MAX, -self.der_obj.der_file.NP_P_MAX, f'', fontsize=14)
        # self.time=-2

        self.plot_points = pd.DataFrame(self.plot_points_dict)
        self.meas_points = pd.DataFrame(self.meas_points_dict)

        if pu:
            for i, point in self.plot_points.iterrows():
                self.ax_pq.scatter(self.plot_points['p_out_pu'].values[i],
                                   self.plot_points['q_out_pu'].values[i], s=60, marker='^', color='blue')
            for i, point in self.meas_points.iterrows():
                self.ax_pq.scatter(self.meas_points['P'].values[i],
                                self.meas_points['Q'].values[i],
                                   marker='v',
                                s=60, color='purple')
        else:
            for i, point in self.plot_points.iterrows():
                self.ax_pq.scatter(self.plot_points['p_out_pu'].values[i]*self._kva,
                                             self.plot_points['q_out_pu'].values[i]*self._kva, s=60, color='blue')
                for i, point in self.meas_points.iterrows():
                    self.ax_pq.scatter(self.meas_points['P'].values[i]*self._kva,
                                       self.meas_points['Q'].values[i]*self._kva,
                                       marker='v',
                                       s=60, color='purple')







        if self.der_obj.der_file.CONST_PF_MODE_ENABLE:
            pf=self.der_obj.der_file.CONST_PF
            if self.der_obj.der_file.CONST_PF_EXCITATION == "INJ":
                sign = 1
            elif self.der_obj.der_file.CONST_PF_EXCITATION == "ABS":
                sign = -1

            if pu:
                p = pf
                q = sign * np.sqrt(1 - pf ** 2)
            else:
                p = self._kva * pf
                q = sign * self._kva * np.sqrt(1 - pf ** 2)
            if type(self.der_obj) is opender.DER_BESS:
                self.const_pf_fig_obj, =self.ax_pq.plot([-p, p], [-q, q], color='yellow', label=f"{pf} Power Factor")
            else:
                self.const_pf_fig_obj, =self.ax_pq.plot([0, p], [0, q], color='yellow', label=f"{pf} Power Factor")
        else:
            self.const_pf_fig_obj,  = self.ax_pq.plot([], [], color='yellow')

        if self.der_obj.der_file.QP_MODE_ENABLE:
            p1 = self.calc_kw(self.der_obj.der_file.QP_CURVE_P1_GEN)
            p2 = self.calc_kw(self.der_obj.der_file.QP_CURVE_P2_GEN)
            p3 = self.calc_kw(self.der_obj.der_file.QP_CURVE_P3_GEN)
            q1 = self.calc_kvar(self.der_obj.der_file.QP_CURVE_Q1_GEN)
            q2 = self.calc_kvar(self.der_obj.der_file.QP_CURVE_Q2_GEN)
            q3 = self.calc_kvar(self.der_obj.der_file.QP_CURVE_Q3_GEN)
            if pu:
                [p1, p2, p3, q1, q2, q3] = [i/self._kva for i in [p1, p2, p3, q1, q2, q3]]
            if type(self.der_obj) is opender.DER_BESS:
                p_1 = self.der_obj.der_file.QP_CURVE_P1_LOAD * self.der_file.NP_P_MAX_CHARGE
                p_2 = self.der_obj.der_file.QP_CURVE_P2_LOAD * self.der_file.NP_P_MAX_CHARGE
                p_3 = self.der_obj.der_file.QP_CURVE_P3_LOAD * self.der_file.NP_P_MAX_CHARGE
                q_1 = self.calc_kvar(self.der_obj.der_file.QP_CURVE_Q1_LOAD)
                q_2 = self.calc_kvar(self.der_obj.der_file.QP_CURVE_Q2_LOAD)
                q_3 = self.calc_kvar(self.der_obj.der_file.QP_CURVE_Q3_LOAD)
                [p_1, p_2, p_3, q_1, q_2, q_3] = [i/self._kva for i in [p_1, p_2, p_3, q_1, q_2, q_3]]
                self.qp_curve_fig_obj, = self.ax_pq.plot([-self._kva, p_3, p_2, p_1, p1, p2, p3, self._kva], [q_3, q_3, q_2, q_1, q1, q2, q3, q3], color='orange', label='Watt-var')
            else:
                self.qp_curve_fig_obj, = self.ax_pq.plot([0, p1, p2, p3, self._kva], [q1, q1, q2, q3, q3], color='orange', linewidth=2, label='Watt-var')

        else:
            self.qp_curve_fig_obj, = self.ax_pq.plot([], [], color='yellow', label='')

        if self.der_obj.der_file.AP_LIMIT_ENABLE:
            p = self.calc_kw(self.der_obj.der_file.AP_LIMIT)
            self.ap_limit_fig_obj, = self.ax_pq.plot([p,p], [-self._kva, self._kva], color='brown', label='P limit')
        else:
            self.ap_limit_fig_obj, = self.ax_pq.plot([], [], color='brown', label='')

        if type(self.der_obj) is opender.DER_BESS:
            self.ax_pq.legend(loc=1)
        else:
            self.ax_pq.legend(loc=2)
    def animate(self, i):
        self.point.remove()  # update the ata

        if i>=len(self.plot_points):
            i=len(self.plot_points)-1
        self.point = self.ax_pq.scatter(self.plot_points['p_out_kw'].values[i],
                                     self.plot_points['q_out_kvar'].values[i], s=60, color='blue')

        self.point_hollow.remove()
        self.point_hollow = self.ax_pq.scatter(self.calc_kw(self.plot_points['p_desired_pu'].values[i]),
                                            self.calc_kvar(self.plot_points['q_desired_pu'].values[i]), s=80,
                                            facecolors='none', edgecolors='green')
        # print(self.const_pf_fig_obj)
        v=self.plot_points['v_meas_pu'].values[i]
        self.time_text.set_text(f't={(i-2)*opender.der.DER.t_s:.1f}\r\nv_pu={v:.1f}')

        if self.plot_points['CONST_PF_MODE_ENABLE'].values[i]:
            pf=self.plot_points['CONST_PF'].values[i]

            if self.plot_points['CONST_PF_EXCITATION'].values[i]== "INJ":
                sign = 1
            elif self.plot_points['CONST_PF_EXCITATION'].values[i] == "ABS":
                sign = -1

            p = self._kva * pf
            q = sign * self._kva * np.sqrt(1 - pf ** 2)
            self.const_pf_fig_obj.remove()
            self.const_pf_fig_obj, = self.ax_pq.plot([0, p], [0, q], color='yellow', label=f"{pf} Power Factor")
        else:
            self.const_pf_fig_obj.remove()
            self.const_pf_fig_obj, = self.ax_pq.plot([], [], color='yellow')

        return self.point, self.point_hollow, self.time_text,self.const_pf_fig_obj



    def prepare_vq_plot(self, pu=True):
        self.fig_vq, self.ax_vq = plt.subplots(nrows=1, ncols=1)
        self.plot_points = pd.DataFrame(self.plot_points_dict)
        v_curve = np.array([0.89, self.der_file.QV_CURVE_V1, self.der_file.QV_CURVE_V2, self.der_file.QV_CURVE_V3,
                            self.der_file.QV_CURVE_V4, 1.1])
        q_curve = np.array(
            [self.der_file.QV_CURVE_Q1, self.der_file.QV_CURVE_Q1, self.der_file.QV_CURVE_Q2, self.der_file.QV_CURVE_Q3,
             self.der_file.QV_CURVE_Q4, self.der_file.QV_CURVE_Q4])

        if self.meas_points_dict != []:
            self.meas_points = pd.DataFrame(self.meas_points_dict)
        else:
            self.meas_points = pd.DataFrame()

        if pu:
            for i, point in self.plot_points.iterrows():
                self.ax_vq.scatter(self.plot_points['v_meas_pu'].values[i],
                                self.plot_points['q_out_pu'].values[i],
                                   marker='^',
                                s=60, color='blue')

            for i, point in self.meas_points.iterrows():
                self.ax_vq.scatter(self.meas_points['V'].values[i],
                                self.meas_points['Q'].values[i],
                                   marker='v',
                                s=60, color='purple')

            self.ax_vq.plot(v_curve, q_curve, color='red', label='Volt-Var Curve')
            self.set_title_labels(self.ax_vq, 'Volt-var', "Voltage (pu)", "Reactive Power (pu)")
        else:
            for i, point in self.plot_points.iterrows():
                self.ax_vq.scatter(self.plot_points['v_meas_pu'].values[i],
                                   self.calc_kvar(self.plot_points['q_out_pu'].values[i]),
                                   marker='^',
                                   s=60, color='blue')

            for i, point in self.meas_points.iterrows():
                self.ax_vq.scatter(self.meas_points['V'].values[i],
                                self.meas_points['Q'].values[i],
                                   marker='v',
                                s=60, color='purple')

            q_curve = [self.calc_kvar(q) for q in q_curve]

            self.ax_vq.plot(v_curve, q_curve, color='red', label='Volt-Var Curve')
            self.set_title_labels(self.ax_vq, 'Volt-var', "Voltage (pu)", "Reactive Power (kvar)")

        self.ax_vq.legend(loc=1)

    def prepare_vp_plot(self):
        self.fig_vp, self.ax_vp = plt.subplots(nrows=1, ncols=1)
        self.plot_points = pd.DataFrame(self.plot_points_dict)
        for i, point in self.plot_points.iterrows():
            self.ax_vp.scatter(self.plot_points['v_meas_pu'].values[i],
                            self.plot_points['p_out_kw'].values[i],
                            s=60, color='blue')

        v_curve = np.array([0.98, self.der_file.PV_CURVE_V1, self.der_file.PV_CURVE_V2, 1.12])

        p_curve = np.array(
            [self.calc_kw(self.der_file.PV_CURVE_P1),
             self.calc_kw(self.der_file.PV_CURVE_P1),
             self.calc_kw(self.der_file.PV_CURVE_P2),
             self.calc_kw(self.der_file.PV_CURVE_P2)])

        self.ax_vp.plot(v_curve, p_curve, color='red', label='Volt-Watt Curve')

        if self.der_obj.der_file.AP_LIMIT_ENABLE:
            p = self.calc_kw(self.der_obj.der_file.AP_LIMIT)
            self.ap_limit_fig_obj, = self.ax_vp.plot([0.98,1.12], [p, p], color='brown', label='P limit')
        else:
            self.ap_limit_fig_obj, = self.ax_vp.plot([], [], color='brown', label='')

        if type(self.der_obj) is opender.DER_BESS:
            self.ax_vp.plot([0.9,1.15],[0,0], color = 'black')

        self.ax_vp.legend(loc=1)
        self.ax_vp.set_xlim([0.97, 1.13])

        self.set_title_labels(self.ax_vp, 'Volt-watt', "Voltage (pu)", "Active Power (kW)")




    def prepare_v3_plot(self,l2l=False, xy=None):

        self.fig_v3, self.ax_v3 = plt.subplots(nrows=1, ncols=1)
        import math
        from matplotlib.patches import FancyArrowPatch

        if xy is None:
            x_a = self.der_obj.der_input.v_a * math.cos(self.der_obj.der_input.theta_a) / self.der_file.NP_AC_V_NOM
            y_a = self.der_obj.der_input.v_a * math.sin(self.der_obj.der_input.theta_a) / self.der_file.NP_AC_V_NOM
            x_b = self.der_obj.der_input.v_b * math.cos(self.der_obj.der_input.theta_b) / self.der_file.NP_AC_V_NOM
            y_b = self.der_obj.der_input.v_b * math.sin(self.der_obj.der_input.theta_b) / self.der_file.NP_AC_V_NOM
            x_c = self.der_obj.der_input.v_c * math.cos(self.der_obj.der_input.theta_c) / self.der_file.NP_AC_V_NOM
            y_c = self.der_obj.der_input.v_c * math.sin(self.der_obj.der_input.theta_c) / self.der_file.NP_AC_V_NOM
        else:
            x_a = xy[0] * math.cos(xy[3])
            x_b = xy[1] * math.cos(xy[4])
            x_c = xy[2] * math.cos(xy[5])
            y_a = xy[0] * math.sin(xy[3])
            y_b = xy[1] * math.sin(xy[4])
            y_c = xy[2] * math.sin(xy[5])



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

    def prepare_pf_plot(self, p_pre_list, p_avl_list=None, pu=True):

        self.fig_pf, self.ax_pf = plt.subplots(nrows=1, ncols=1)

        self.plot_points = pd.DataFrame(self.plot_points_dict)
        colors = ['red', 'blue', 'purple', 'orange']

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

            if -(f4 - 60 - self.der_file.PF_DBOF)/self.der_file.PF_KOF/60 + p_pre <= self.der_file.NP_P_MIN_PU:
                p4 = self.der_file.NP_P_MIN_PU
                p3 = self.der_file.NP_P_MIN_PU
                f3 = ( p_pre- self.der_file.NP_P_MIN_PU) * self.der_file.PF_KOF*60 +60 + self.der_file.PF_DBOF
            else:
                f3 = f4
                p4 = p3 = -(f4 - 60 - self.der_file.PF_DBOF)/self.der_file.PF_KOF/60 + p_pre


            f_curve = [f1, f2, 60-self.der_file.PF_DBUF, 60, 60+self.der_file.PF_DBOF, f3, f4]

            p_curve = [p1, p2, p_pre, p_pre, p_pre, p3, p4]

            self.ax_pf.plot(f_curve, p_curve)

        if self.meas_points_dict != []:
            self.meas_points = pd.DataFrame(self.meas_points_dict)
        else:
            self.meas_points = pd.DataFrame()

        self.ax_pf.plot([self.der_file.UF2_TRIP_F, self.der_file.UF2_TRIP_F], [-1.1, 1.1], color='gray', linestyle='--')
        self.ax_pf.plot([self.der_file.OF2_TRIP_F, self.der_file.OF2_TRIP_F], [-1.1, 1.1], color='gray', linestyle='--')
        self.ax_pf.plot([self.der_file.UF1_TRIP_F, self.der_file.UF1_TRIP_F], [-1.1, 1.1], color='gray', linestyle='-.')
        self.ax_pf.plot([self.der_file.OF1_TRIP_F, self.der_file.OF1_TRIP_F], [-1.1, 1.1], color='gray', linestyle='-.')


        for i, point in self.plot_points.iterrows():
            self.ax_pf.scatter(self.plot_points['freq_hz'].values[i],
                               self.plot_points['p_out_pu'].values[i],
                               marker='^',
                               s=60, color='blue')

        for i, point in self.meas_points.iterrows():
            self.ax_pf.scatter(self.meas_points['F'].values[i],
                               self.meas_points['P'].values[i],
                               marker='v',
                               s=60, color='purple')

        self.ax_pf.legend(loc=1)
        self.ax_pf.set_ylim(0,1.05)
        self.set_title_labels(self.ax_pf, 'Freq-droop', "Frequency (Hz)", "Active Power (pu)")

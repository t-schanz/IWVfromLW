#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr  5 13:57:15 2017

@author: Theresa Lang

This script uses PSRAD to calculate heatingrates for a FASCOD atmosphere
"""
from os.path import join
import matplotlib.pyplot as plt
import numpy as np
import typhon as tp
from sfc_fluxes2 import get_sadata_atmosphere

import psrad


def get_fascod_atmosphere(fascod_path, season):
    """Returns the temperature profile and mixing ratio profiles for H2O, O3,
    N2O, CO, CH4 from a standard sounding or any other giving sounding.
    Instead of returning specific values, interpolated functions are returned.

    Parameters:
        fascod_path (str):
        season (str):

    Returns:
        dict:
    """
    columns = ['t', 'z', 'H2O', 'CO2', 'O3', 'N2O', 'CO', 'CH4']
    atmosphere = {}

    for name in columns:
        path = join(fascod_path, season, '{}.{}.xml'.format(season, name))
        f = tp.arts.xml.load(path)
        pres = f.grids[0]
        atmosphere[name] = f.data.reshape(-1)

    atmosphere['p'] = pres

    return atmosphere


def calc_hr(soundings, spec_range, const_albedo=0.05, zenith_angle=53):
    """Computes the lw radiation for a given sounding.

    Parameters:
        soundings:   profiles of pressure, Temperature, altitude and VMRs of
                     apsorption species in a dictionary
        spec_range   spectral range: 'lw' (longwave) or 'sw' (shortwave)
        const_albedo:surface albedo (constant for all wavelengths)
        zenith_angle:solar zenith angle in degrees (between 0 and 90)
    """
    H2O = soundings['H2O'][:] * 1e6  # in ppm
    CO2 = soundings['CO2'][:] * 1e6
    O3 = soundings['O3'][:] * 1e6
    N2O = soundings['N2O'][:] * 1e6
    CO = soundings['CO'][:] * 1e6
    CH4 = soundings['CH4'][:] * 1e6
    Z = soundings['z'][:]  # in m
    T = soundings['t'][:]  # in K
    P = soundings['p'][:] / 100   # in hPa

    dmy_indices = np.asarray([0])
    ic = dmy_indices.astype("int32") + 1
    c_lwc = np.asarray([0.])
    c_iwc = np.asarray([0.])
    c_frc = np.asarray([0.])

    P_sfc = soundings['p'][0] / 100
    T_sfc = soundings['t'][0]

    albedo = const_albedo
    zenith = zenith_angle
    nlev = len(P)

    psrad.setup_single(nlev, len(ic), ic, c_lwc, c_iwc, c_frc, zenith, albedo,
                       P_sfc, T_sfc, Z, P, T, H2O, O3, CO2, N2O, CO, CH4)

    if spec_range == 'lw':
        psrad.advance_lrtm()
        hr, hr_clr, flxd, flxd_clr, flxu, flxu_clr = psrad.get_lw_fluxes()

        xhr = hr[0, :]
        xhr_clr = hr_clr[0, :]
        xhr[0] = 0
        xhr_clr[0] = 0

        data = {}
        data['hr'] = xhr
        data['hr_clr'] = xhr_clr
        data['flxu'] = flxu[0, :]
        data['flxd'] = flxd[0, :]
        data['flxu_clr'] = flxu_clr[0, :]
        data['flxd_clr'] = flxd_clr[0, :]

    else:
        psrad.advance_srtm()
        (hr, hr_clr, flxd, flxd_clr, flxu, flxu_clr, vis_frc,
         par_dn, nir_dff, vis_diff, par_diff) = psrad.get_sw_fluxes()

        xhr = hr[0, :]
        xhr_clr = hr_clr[0, :]
        xhr[0] = 0
        xhr_clr[0] = 0

        data = {}
        data['hr'] = xhr[::-1]
        data['hr_clr'] = xhr_clr[::-1]
        data['flxu'] = flxu[0, ::-1]
        data['flxd'] = flxd[0, ::-1]
        data['flxu_clr'] = flxu_clr[0, ::-1]
        data['flxd_clr'] = flxd_clr[0, ::-1]

    return data


if __name__ == '__main__':
    atms = ['tropical','subarctic-winter']
    print("Standard:")
    for atm in atms:
        fascod_atm = get_sadata_atmosphere(atm)
        results_lw = calc_hr(fascod_atm, 'lw')


        print(atm, results_lw["flxd_clr"][0],fascod_atm['p'][0])

    print("No water:")

    for atm in atms:
        fascod_atm = get_sadata_atmosphere(atm)
        fascod_atm["H2O"] = np.multiply(fascod_atm["H2O"], 0)
        results_lw = calc_hr(fascod_atm, 'lw')

        print(atm ,results_lw["flxd_clr"][0], fascod_atm['p'][0])


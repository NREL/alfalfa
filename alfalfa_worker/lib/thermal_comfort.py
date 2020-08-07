# Copyright 2019
# Author: Nicholas Long
# This class calculates the predicted mean vote and percent people dissatisfied based on the methodology in
# ASHRAE Standard 55 Normative Appendix B and in accordance with ISO 7730.

import math


class ThermalComfort(object):
    def __init__(self):
        super()

    @classmethod
    def pmv_ppd(cls, ta, tr, met, clo, vel, rh, wme=0):
        """
        :param ta: float, Air Temperature (C)
        :param tr: float, mean radiant temperature (C)
        :param met: float, metabolic rate (met)
        :param clo: float, clothing (clo)
        :param vel: float, relative air velocity (m/s)
        :param rh: float, percent relative humidity (%)
        :param wme: float, external work (met), defaults to 0
        :return: list, [PMV, PPD]
        """
        # water vapor pressure (Pascals)
        pa = rh * 10 * math.exp(16.6536 - 4030.183 / (ta + 235))

        # thermal insulation of the clothing in m2K/W
        icl = 0.155 * clo

        # metabolic rate in W/m2
        m = met * 58.15

        # external work in W/m2
        w = wme * 58.15

        # internal heat production in the human body
        mw = m - w

        # clothing area factor
        fcl = 1 + 1.29 * icl if icl < 0.078 else 1.05 + 0.645 * icl

        # heat transfer coefficienct by forced convection
        hcf = 12.1 * math.sqrt(vel)

        # air temperatures in Kelvin
        taa = ta + 273
        tra = tr + 273

        # Calculate surface temperature of clothing by iteration
        # tcl = f(taa, ...)
        tcla = taa + (35.5 - ta) / (3.5 * (6.45 * icl + 0.1))
        p1 = icl * fcl
        p2 = p1 * 3.96
        p3 = p1 * 100
        p4 = p1 * taa
        p5 = 308.7 - 0.028 * mw + p2 * (tra / 100) ** 4
        xn = tcla / 100
        # initial guess for xf is xn / 2
        xf = xn / 2
        n = 0
        eps = 0.00015

        while abs(xn - xf) > eps:
            n += 1
            xf = (xf + xn) / 2
            hcn = 2.38 * abs(100 * xf - taa) ** 0.25
            hc = hcf if hcf > hcn else hcn
            xn = (p5 + p4 * hc - p2 * xf ** 4) / (100 + p3 * hc)

            if n > 150:
                raise Exception('Unable to converge on clothing surface temperature')

        # final surface temperature of clothing
        tcl = 100 * xn - 273

        # heat loss components
        # skin
        hl1 = 3.05 * 0.001 * (5733 - (6.99 * mw) - pa)
        # sweating
        hl2 = 0.42 * (mw - 58.15) if mw > 58.15 else 0
        # latent respiration heat loss
        hl3 = 1.7 * 0.00001 * m * (5867 - pa)
        # dry respiration heat loss
        hl4 = 0.0014 * m * (34 - ta)
        # heat loss by radiation
        hl5 = 3.96 * fcl * (xn ** 4 - (tra / 100) ** 4)
        # heat loss by convection
        hl6 = fcl * hc * (tcl - ta)

        # caluate PMV
        ts = 0.303 * math.exp(-0.036 * m) + 0.028
        pmv = ts * (mw - hl1 - hl2 - hl3 - hl4 - hl5 - hl6)
        ppd = 100 - 95 * math.exp(-0.03353 * pmv ** 4 - 0.2179 * pmv ** 2)
        return [pmv, ppd]

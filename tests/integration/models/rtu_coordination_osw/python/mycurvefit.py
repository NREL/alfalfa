import numpy as np
import csv


def fit_sat_sst(sat, sst):
    """get the curve fit between supply-air-temp and saturated-suction-temp"""
    z = np.polyfit(sat, sst, 4)
    #print('coefcients: ', type(z), z.tolist())
    p = np.poly1d(z)
    with open('coeff_SAT_SST_emerson_001.csv', 'w') as fh:
        writer = csv.writer(fh, delimiter=',')
        writer.writerow(['x4', 'x3', 'x2', 'x1', 'x0'])
        writer.writerow(z.tolist())

    return p


def fit_sat_sct(sat, sct):
    """get the curve fit between supply-air-temp and saturated-condensing-temp"""
    z = np.polyfit(sat, sct, 4)
    #print('coefficients: ', z.tolist())
    p = np.poly1d(z)
    with open('coeff_SAT_SCT_emerson_001.csv', 'w') as fh:
        writer = csv.writer(fh, delimiter=',')
        writer.writerow(['x4', 'x3', 'x2', 'x1', 'x0'])
        writer.writerow(z.tolist())

    return p

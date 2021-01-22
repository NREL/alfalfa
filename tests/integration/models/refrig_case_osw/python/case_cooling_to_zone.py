
def case_cooling_to_zone(T_case_air, T_zone):
    """
    This function is to calculate the case thermal load release to zones.
    input: T_case_air, case internal air temperature
    input: T_zone, zone/ambient air temperature
    output: Q,
    """
    """
    notes:
    (1) case air temperature is the average temperature
    (2) if Q<0, it means cooling goes to zone; if Q>0, it means heating goes to zone.
    (3) in the future, we will add heat release from infiltration, open/shut items...
    """
    # areas of all 6 surfaces of case (experiment):
    a1 = 2
    a2 = 8
    a3 = 5
    a4 = a1
    a5 = a2
    a6 = a3
    # heat convection coefficient for 6 external surfaces (from experiment):
    h1 = 10
    h2 = 12
    h3 = 20
    h4 = 10
    h5 = 12
    h6 = 20

    U_external = 1/(h1*a1) + 1/(h2*a2) + 1/(h3*a3) + 1/(h4*a4) + 1/(h5*a5) + 1/(h6*a6)

    # case thickness of 6 surfaces
    d1 = 0.01
    d2 = 0.02
    d3 = 0.005
    d4 = d1
    d5 = d2
    d6 = d3

    # case conduction coeffiient of 6 surfaces
    k1 = 12.5
    k2 = 15.2
    k3 = 17.3
    k4 = k1
    k5 = k2
    k6 = k3

    U_conduction = d1/(k1*a1) + d2/(k2*a2) + d3/(k3*a3) + d4/(k4*a4) + d5/(k5*a5) + d6/(k6*a6)

    # convection coefficient for internal surface (from experiment)
    h_in = 30
    U_internal = 1/(h_in * (a1+a2+a3+a4+a5+a6))

    # overall transfer coefficient
    U = 1 / (U_external + U_conduction + U_internal)
    print ('overall hat transfer coeff: ', U)
    # heating/cooling release to zone
    Q = U * (T_case_air-T_zone)

    return Q


##############################################
#      exmaple to run the function           #
Q = case_cooling_to_zone(2, 29)
print(Q)
##############################################

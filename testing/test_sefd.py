import pytest


def test_SEFD():
    from src.functions.calculations import SEFD 
    import astropy.units as u
    import numpy as np

    T_sys = 270 * u.K
    radius = 25 * u.m
    area = np.pi * radius**2
    eta_A = 1

    sefd = SEFD.calculate(T_sys, area, eta_A).value
    assert sefd == 3.797057313069965e-24
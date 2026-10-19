"""Vertical shoe profile around the connector shell centre at Z = -0.5 mm."""
import math


def guide_vertical_profile(upper,throat=.0073):
    if not math.isfinite(throat) or not .0072<=throat<=.009:
        raise ValueError('Guide throat must be between 7.2 and 9 mm')
    delta=(throat-.0073)/2
    land=.00395+delta
    section=(.00315+delta,.00395+delta,.00475+delta,.00475+delta)
    if not upper:
        land=-land-.001
        section=tuple(-z-.001 for z in section)
    return land,section

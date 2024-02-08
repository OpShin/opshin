"""
A special libary that gives access to a function that checks the integrity of PlutusDatum objects.
"""

from pycardano import PlutusData


def check_integrity(x: PlutusData) -> None:
    """
    Checks the integrity of a PlutusDatum object.
    In particular, it takes an object of any type and checks that
    - the constructor id matches the id defined in the type
    - the fields specified in the type are present
    - no additional fields are present

    This has no equivalent in Python.
    """
    pass

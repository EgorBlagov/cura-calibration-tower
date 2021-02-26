import os

__version__ = '1.0.0'

if 'CALIBRATION_TOWER_DEBUG' in os.environ:
    from .script import CalibrationTower

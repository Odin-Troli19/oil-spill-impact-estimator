"""
Oil Spill Impact Estimator - Models Package
-------------------------------------------
This package contains the core models used for simulating oil spill
dispersal and estimating environmental impacts.
"""

from .dispersal_model import OilDispersalModel
from .impact_estimator import ImpactEstimator

__all__ = ['OilDispersalModel', 'ImpactEstimator']
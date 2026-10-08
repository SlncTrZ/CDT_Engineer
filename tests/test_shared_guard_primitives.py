"""Rule-of-Two tests for shared deterministic guard primitives."""
import math
import unittest

from domains.guard_primitives import GuardInputError, convert_value, finite_number, unit_ratio
from domains.site_reconstruction.guards import GuardInputError as SiteGuardInputError
from domains.mechanical_reconstruction.guards import GuardInputError as MechanicalGuardInputError

class SharedGuardPrimitiveTests(unittest.TestCase):
    def test_domains_share_one_guard_input_error_type(self):
        self.assertIs(SiteGuardInputError, GuardInputError)
        self.assertIs(MechanicalGuardInputError, GuardInputError)

    def test_finite_number_rejects_nan_infinity_and_bool(self):
        for value in [math.nan, math.inf, -math.inf, '1', True, False]:
            with self.assertRaises(GuardInputError):
                finite_number(value,'value')

    def test_unit_ratio_matches_engineering_units(self):
        self.assertAlmostEqual(0.001,unit_ratio('mm','m'))
        self.assertAlmostEqual(25.4,unit_ratio('in','mm'))

    def test_convert_value_is_directionally_explicit(self):
        self.assertAlmostEqual(25.4,convert_value(1.0,'in','mm'))
        self.assertAlmostEqual(1.0,convert_value(1000.0,'mm','m'))

if __name__=='__main__': unittest.main()

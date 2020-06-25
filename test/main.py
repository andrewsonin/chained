"""
Defines unit-tests for 'chained/__init__.py' that cannot be implemented inside docstrings.
"""
from unittest import TestCase

from chained import seq


class Seq(TestCase):
    def test_wrong_ellipsis_position(self):
        self.assertRaisesRegex(
            IndexError,
            'Ellipsis can be a placeholder only at the 1st or the 2nd index positions',
            lambda: seq(..., 2, 32)
        )
        self.assertRaisesRegex(
            IndexError,
            'Ellipsis can be a placeholder only at the 1st or the 2nd index positions',
            lambda: seq(..., 2, 32, 5000)
        )
        self.assertRaisesRegex(
            IndexError,
            'Ellipsis can be a placeholder only at the 1st or the 2nd index positions',
            lambda: seq(..., 2, 32, 5000, last=23)
        )
        self.assertRaisesRegex(
            IndexError,
            'Ellipsis can be a placeholder only at the 1st or the 2nd index positions',
            lambda: seq(2, 32, 22, ...)
        )
        self.assertRaisesRegex(
            IndexError,
            'Ellipsis can be a placeholder only at the 1st or the 2nd index positions',
            lambda: seq('ewewr', 2, 32, 22, ...)
        )
        self.assertRaisesRegex(
            IndexError,
            'Ellipsis can be a placeholder only at the 1st or the 2nd index positions',
            lambda: seq('ewewr', 2, 32, 22, ..., last='321')
        )

    def test_wrong_last_definition(self):
        self.assertRaisesRegex(
            ValueError,
            "Parameter 'last' should not be defined if positional arguments obey the following pattern:",
            lambda: seq(23, ..., 32, last='some')
        )
        self.assertRaisesRegex(
            ValueError,
            "Parameter 'last' should not be defined if positional arguments obey the following pattern:",
            lambda: seq(23, 323, ..., 32, last=1)
        )

    def test_wrong_num_pos_args(self):
        self.assertRaisesRegex(
            IndexError,
            'The number of positional arguments should not exceed 3 ',
            lambda: seq(23, ..., 32, 32)
        )
        self.assertRaisesRegex(
            IndexError,
            'The number of positional arguments should not exceed 3 ',
            lambda: seq(23, ..., 32, 32, 233232)
        )
        self.assertRaisesRegex(
            IndexError,
            'The number of positional arguments should not exceed 4 ',
            lambda: seq(23, 2323, ..., 32, 3)
        )
        self.assertRaisesRegex(
            IndexError,
            'The number of positional arguments should not exceed 4 ',
            lambda: seq(23, 2323, ..., 32, 3, 3232)
        )

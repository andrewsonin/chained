import copy
import unittest
from typing import Final

from lib import functions
from lib.errors.functions import InfiniteSelfReferenceError


class TestFlat(unittest.TestCase):
    init_tuple: Final = (3, 4, -1, [232, None, 'Jim', (3, [333, [333, 43]], b'Gregor')])
    init_list: Final = [3, 4, -1, [232, None, 'Jim', (3, [333, [333, 43]], b'Gregor')]]

    result_tuple: Final = (3, 4, -1, 232, None, 'Jim', 3, 333, 333, 43, b'Gregor')
    result_list: Final = [3, 4, -1, 232, None, 'Jim', 3, 333, 333, 43, b'Gregor']

    def test_flat(self):
        array = copy.deepcopy(self.init_tuple)
        self.assertEqual(
            tuple(functions.flat(array)),
            self.result_tuple
        )
        self.assertEqual(
            list(functions.flat(array)),
            self.result_list
        )
        self.assertEqual(array, self.init_tuple)

        array = copy.deepcopy(self.init_list)
        self.assertEqual(
            tuple(functions.flat(array)),
            self.result_tuple
        )
        self.assertEqual(
            list(functions.flat(array)),
            self.result_list
        )
        self.assertEqual(array, self.init_list)

    def test_has_inf_recursion(self):
        array = copy.deepcopy(self.init_tuple)
        self.assertFalse(functions.has_inf_recursion(array))
        self.assertEqual(array, self.init_tuple)

        array[-1].append(array)
        self.assertTrue(functions.has_inf_recursion(array))

    def test_flat_with_rec_check(self):
        array = copy.deepcopy(self.init_tuple)
        self.assertEqual(
            tuple(functions.flat_with_rec_check(array)),
            self.result_tuple
        )
        self.assertEqual(
            list(functions.flat_with_rec_check(array)),
            self.result_list
        )
        self.assertEqual(array, self.init_tuple)

        array[-1].append(array)
        self.assertRaisesRegex(
            InfiniteSelfReferenceError,
            'Iterable contains a reference to itself',
            lambda: tuple(functions.flat_with_rec_check(array))
        )


class TestCompose(unittest.TestCase):
    def test_compose_map(self):
        self.assertEqual(
            tuple(
                functions.compose_map(
                    (
                        lambda x: x ** 2,
                        lambda x: x - 1,
                        round
                    ),
                    (1, 2, 3, 4, 8, 10)
                )
            ),
            (0, 3, 8, 15, 63, 99)
        )

    def test_compose_multiarg_map(self):
        self.assertEqual(
            tuple(
                functions.compose_multiarg_map(
                    (
                        lambda x, y:     (x * y, x - y, x + y),
                        lambda x, y, z:   x + y + z,
                        lambda x:        [x * x, x * 2],
                        lambda array:     sum(array)
                    ),
                    (
                        (1, 2),
                        (3, 4),
                        (5, 6)
                    )
                )
            ),
            (24, 360, 1680)
        )

    def test_compose_filter(self):
        self.assertEqual(
            tuple(
                functions.compose_filter(
                    (
                        lambda x: x > 2,
                        lambda x: x < 10
                    ),
                    (1, 2, 3, 4, 8, 10)
                )
            ),
            (3, 4, 8)
        )

    def test_compose_multiarg_filter(self):
        self.assertEqual(
            tuple(
                functions.compose_multiarg_filter(
                    (
                        lambda x, y:     (x * y, x - y, x + y),
                        lambda x, y, z:   x + y + z,
                        lambda x:        [x * x, x * 2],
                        lambda array:     sum(array)
                    ),
                    (
                        (1,  2),  # 24    will be passed
                        (-1, 0),  # 0     won't
                        (3,  4),  # 360   will be passed
                        (5,  6),  # 1680  will be passed
                        (0,  0)   # 0     won't
                    )
                )
            ),
            ((1, 2), (3, 4), (5, 6))
        )

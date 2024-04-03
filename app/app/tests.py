from django.test import SimpleTestCase

from app import calc


class CalsTests(SimpleTestCase):

    def test_plus(self):
        result = calc.plus(3, 4)
        self.assertEqual(result, 7)

    def test_subtract(self):
        result = calc.subtract(10, 16)
        self.assertEqual(result, 6)

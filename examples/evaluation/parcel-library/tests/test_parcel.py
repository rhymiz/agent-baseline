import unittest
from parcel import Parcel, State, complete


class ParcelTests(unittest.TestCase):
    def test_completion_preserves_identity_and_original(self):
        original = Parcel("sample", State.QUEUED)
        completed = complete(original)
        self.assertEqual(completed, Parcel("sample", State.COMPLETED))
        self.assertEqual(original.state, State.QUEUED)

    def test_completed_parcel_is_rejected(self):
        with self.assertRaises(ValueError):
            complete(Parcel("sample", State.COMPLETED))

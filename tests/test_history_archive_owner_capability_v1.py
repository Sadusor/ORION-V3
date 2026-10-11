"""Isolated owner-capability tests, no production enrollment."""
import tempfile
import unittest
from pathlib import Path
from src.orion_v3.modules.history_archive_owner_capability_v1 import OwnerCapabilityV1


class OwnerCapabilityTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.owner = OwnerCapabilityV1(Path(temp.name))

    def test_not_enrolled_fails_closed(self):
        self.assertFalse(self.owner.verify("x" * 60))

    def test_enrollment_requires_physical_confirmation(self):
        with self.assertRaises(PermissionError):
            self.owner.enroll()
        self.assertFalse(self.owner.enrolled())

    def test_enroll_and_verify(self):
        secret = self.owner.enroll(physically_confirmed=True)
        self.assertTrue(self.owner.verify(secret))
        self.assertFalse(self.owner.verify("paired-device"))
        self.assertFalse(self.owner.verify(secret + "changed"))
        self.assertNotIn(secret, self.owner.path.read_text())

    def test_cannot_enroll_twice(self):
        self.owner.enroll(physically_confirmed=True)
        with self.assertRaises(FileExistsError):
            self.owner.enroll(physically_confirmed=True)

    def test_revoke(self):
        secret = self.owner.enroll(physically_confirmed=True)
        with self.assertRaises(PermissionError):
            self.owner.revoke()
        self.assertTrue(self.owner.verify(secret))
        self.owner.revoke(physically_confirmed=True)
        self.assertFalse(self.owner.verify(secret))

    def test_rotate_invalidates_old_secret(self):
        secret = self.owner.enroll(physically_confirmed=True)
        with self.assertRaises(PermissionError):
            self.owner.rotate(current_secret="wrong", physically_confirmed=True)
        new = self.owner.rotate(current_secret=secret, physically_confirmed=True)
        self.assertFalse(self.owner.verify(secret))
        self.assertTrue(self.owner.verify(new))

    def test_restart_persists(self):
        secret = self.owner.enroll(physically_confirmed=True)
        self.assertTrue(OwnerCapabilityV1(self.owner.directory).verify(secret))


if __name__ == "__main__":
    unittest.main()

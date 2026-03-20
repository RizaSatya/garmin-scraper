import tomllib
import unittest
from pathlib import Path


class PackagingConfigTest(unittest.TestCase):
    def test_pyproject_explicitly_limits_package_discovery(self):
        pyproject = tomllib.loads(Path("pyproject.toml").read_text())

        setuptools_config = pyproject["tool"]["setuptools"]
        package_finder = setuptools_config["packages"]["find"]

        self.assertEqual(package_finder["include"], ["garmin_sync*"])
        self.assertEqual(package_finder["exclude"], ["sql*"])

    def test_build_system_declares_wheel(self):
        pyproject = tomllib.loads(Path("pyproject.toml").read_text())

        self.assertIn("wheel", pyproject["build-system"]["requires"])


if __name__ == "__main__":
    unittest.main()

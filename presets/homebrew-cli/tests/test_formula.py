import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/render_formula.py'
spec = importlib.util.spec_from_file_location('formula', SCRIPT)
formula = importlib.util.module_from_spec(spec)
spec.loader.exec_module(formula)


class FormulaTest(unittest.TestCase):
    def test_stable_and_versioned_formulas_parse(self):
        stable, pinned = formula.render('example/my-cli', 'my-cli', '0.1.0', 'a' * 64)
        self.assertIn('/tags/v0.1.0.tar.gz', stable)
        self.assertIn('class MyCli < Formula', stable)
        self.assertIn('class MyCliAT010 < Formula', pinned)
        self.assertIn('keg_only :versioned_formula', pinned)
        self.assertNotIn('  head ', pinned)
        self.assertIn('output: bin/"my-cli"', stable)
        self.assertIn('output: bin/"my-cli"', pinned)
        with tempfile.TemporaryDirectory() as directory:
            for name, source in [('my-cli.rb', stable), ('my-cli@0.1.0.rb', pinned)]:
                path = Path(directory) / name
                path.write_text(source)
                subprocess.run(['ruby', '-c', str(path)], check=True, capture_output=True)

    def test_rejects_unsafe_or_noncanonical_inputs(self):
        valid = ['example/my-cli', 'my-cli', '0.1.0', 'a' * 64]
        for index, value in [(0, '../repo'), (1, '../cli'), (1, 'cli"'),
                             (2, '01.0.0'), (2, 'v0.1.0'), (3, 'invalid')]:
            with self.subTest(index=index, value=value):
                args = valid.copy()
                args[index] = value
                with self.assertRaises(ValueError):
                    formula.render(*args)

    def test_reruns_and_immutable_version(self):
        with tempfile.TemporaryDirectory() as directory:
            args = [sys.executable, str(SCRIPT), '--repository', 'example/my-cli',
                    '--name', 'my-cli', '--version', '0.1.0', '--sha256', 'a' * 64,
                    '--output-dir', directory]
            subprocess.run(args, check=True, capture_output=True)
            subprocess.run(args, check=True, capture_output=True)
            stable = Path(directory) / 'my-cli.rb'
            pinned = Path(directory) / 'my-cli@0.1.0.rb'
            before = (stable.read_bytes(), pinned.read_bytes())
            args[args.index('a' * 64)] = 'b' * 64
            result = subprocess.run(args, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('refusing to overwrite immutable formula', result.stderr)
            self.assertEqual((stable.read_bytes(), pinned.read_bytes()), before)


if __name__ == '__main__':
    unittest.main()

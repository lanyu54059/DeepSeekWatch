import importlib.util
import plistlib
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('package', Path(__file__).resolve().parents[1] / 'Scripts/package.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class BundleValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.host = Path(self.temp.name) / 'DeepSeekPhone.app'
        self.watch = self.host / 'Watch/DeepSeekWatch.app'
        for path, platform, identifier in [(self.host, 'iPhoneOS', 'com.personal.deepseek.phone'),
                                          (self.watch, 'WatchOS', 'com.personal.deepseek.phone.watchkitapp')]:
            path.mkdir(parents=True, exist_ok=True)
            info = {'CFBundleIdentifier': identifier, 'CFBundleExecutable': 'Executable',
                    'CFBundleSupportedPlatforms': [platform]}
            if path == self.watch:
                info.update(WKApplication=True, WKCompanionAppBundleIdentifier='com.personal.deepseek.phone')
            (path / 'Info.plist').write_bytes(plistlib.dumps(info))
            (path / 'Executable').write_bytes(b'\xcf\xfa\xed\xfe' + bytes(64))
            (path / 'Assets.car').write_bytes(b'test fixture, not an actual compiled resource')

    def test_valid_single_target_graph(self):
        self.assertEqual(module.validate(self.host)['extensions'], 0)

    def test_missing_watch_rejected(self):
        self.watch.rename(self.watch.with_suffix('.missing'))
        with self.assertRaises(ValueError): module.validate(self.host)

    def test_broken_companion_rejected(self):
        path = self.watch / 'Info.plist'
        info = plistlib.loads(path.read_bytes())
        info['WKCompanionAppBundleIdentifier'] = 'wrong.host'
        path.write_bytes(plistlib.dumps(info))
        with self.assertRaises(ValueError): module.validate(self.host)

    def test_simulator_rejected(self):
        path = self.watch / 'Info.plist'
        info = plistlib.loads(path.read_bytes())
        info['CFBundleSupportedPlatforms'] = ['WatchSimulator']
        path.write_bytes(plistlib.dumps(info))
        with self.assertRaises(ValueError): module.validate(self.host)

    def test_fake_binary_rejected(self):
        (self.watch / 'Executable').write_bytes(bytes(100))
        with self.assertRaises(ValueError): module.validate(self.host)

if __name__ == '__main__': unittest.main()

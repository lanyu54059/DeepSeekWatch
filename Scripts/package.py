"""Validate compiled bundle graph before producing an explicitly unsigned IPA."""
import json
import plistlib
import shutil
import struct
import sys
import tempfile
import zipfile
from pathlib import Path

def require(condition, message):
    if not condition:
        raise ValueError(message)

def read_bundle(path, platform):
    with (path / 'Info.plist').open('rb') as file:
        info = plistlib.load(file)
    require(platform in info.get('CFBundleSupportedPlatforms', []), f'Wrong SDK/platform: {path}')
    binary = path / info['CFBundleExecutable']
    require(binary.is_file() and binary.stat().st_size > 32, f'Missing executable: {path}')
    with binary.open('rb') as file:
        magic = file.read(4)
    require(magic in (b'\xcf\xfa\xed\xfe', b'\xce\xfa\xed\xfe', b'\xca\xfe\xba\xbe', b'\xca\xfe\xba\xbf'), f'Not Mach-O: {binary}')
    require((path / 'Assets.car').is_file(), f'Missing compiled icon resources: {path}')
    return info

def validate(host):
    phone = read_bundle(host, 'iPhoneOS')
    watches = list((host / 'Watch').glob('*.app'))
    require(len(watches) == 1, 'Exactly one embedded Watch application is required')
    watch = read_bundle(watches[0], 'WatchOS')
    require(phone['CFBundleIdentifier'] == 'com.personal.deepseek.phone', 'Unexpected phone identifier')
    require(watch['CFBundleIdentifier'] == phone['CFBundleIdentifier'] + '.watchkitapp', 'Watch identifier mismatch')
    require(watch.get('WKCompanionAppBundleIdentifier') == phone['CFBundleIdentifier'], 'Broken companion relationship')
    require(watch.get('WKApplication') is True, 'Expected modern single-target Watch app')
    # A modern WKApplication contains its executable directly: no WatchKit extension is required.
    extensions = list(host.rglob('*.appex'))
    for extension in extensions:
        with (extension / 'Info.plist').open('rb') as file:
            info = plistlib.load(file)
        require((extension / info['CFBundleExecutable']).is_file(), f'Missing extension executable: {extension}')
    return {'status': 'PACKAGED_UNSIGNED', 'phone': phone['CFBundleIdentifier'],
            'watch': watch['CFBundleIdentifier'], 'watchTopology': 'single-target WKApplication; no separate extension',
            'extensions': len(extensions), 'signed': False, 'deviceInstallation': 'NOT_VERIFIED'}

def package(host, output):
    report = validate(host)
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        payload = Path(tmp) / 'Payload'
        payload.mkdir()
        shutil.copytree(host, payload / host.name, symlinks=True)
        # ditto preserves executable modes and resource metadata on macOS.
        import subprocess
        destination = (output / 'DeepSeekWatch-unsigned.ipa').resolve()
        subprocess.run(['ditto', '-c', '-k', '--keepParent', str(payload), str(destination)], check=True)
        with zipfile.ZipFile(destination) as archive:
            prefix = f'Payload/{host.name}/'
            require(prefix + 'Info.plist' in archive.namelist(), 'IPA missing Payload host')
            require(any(name.startswith(prefix + 'Watch/') and name.endswith('/Info.plist') for name in archive.namelist()), 'IPA missing embedded Watch')
            require(archive.testzip() is None, 'Corrupt IPA')
    (output / 'validation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    package(Path(sys.argv[1]), Path(sys.argv[2]))

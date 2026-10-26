"""Generate original opaque PNG icons using only Python's standard library."""
import json
import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def png(size=1024):
    rows = bytearray()
    for y in range(size):
        rows.append(0)
        for x in range(size):
            # Blue speech balloon with three white dots on a navy field.
            bubble = (x - 512) ** 2 + (y - 460) ** 2 < 330 ** 2
            tail = 255 < x < 420 and 620 < y < 810 and x + y < 1110
            dot = any((x - cx) ** 2 + (y - 460) ** 2 < 37 ** 2 for cx in (355, 512, 669))
            rows.extend((245, 250, 255) if dot else (25, 112, 245) if bubble or tail else (5, 14, 35))
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', size, size, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(rows)) + chunk(b'IEND', b'')

def main():
    image = png()
    for target, platform in [('DeepSeekPhone', 'ios'), ('DeepSeekWatch', 'watchos')]:
        assets = ROOT / target / 'Assets.xcassets'
        icon = assets / 'AppIcon.appiconset'
        icon.mkdir(parents=True, exist_ok=True)
        (assets / 'Contents.json').write_text(json.dumps({'info': {'author': 'xcode', 'version': 1}}))
        (icon / 'Icon.png').write_bytes(image)
        (icon / 'Contents.json').write_text(json.dumps({
            'images': [{'filename': 'Icon.png', 'idiom': 'universal', 'platform': platform, 'size': '1024x1024'}],
            'info': {'author': 'xcode', 'version': 1}
        }, indent=2))

if __name__ == '__main__':
    main()

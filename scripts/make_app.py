"""Build a double-clickable macOS app next to this folder that starts the trainer and opens the browser.

python3 scripts/make_app.py ["AI-103 lernen"]   needs Pillow and macOS osacompile, iconutil, codesign
"""
import plistlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FONT = "/System/Library/Fonts/Supplemental/Georgia Bold.ttf"


def icon(size=1024):
    """Draw the app icon: an amber card on a darker one, on the trainer's dark background."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    s = size / 1024
    d.rounded_rectangle([40 * s, 40 * s, 984 * s, 984 * s], radius=220 * s, fill=(30, 30, 30))
    back = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(back).rounded_rectangle([250 * s, 230 * s, 790 * s, 710 * s], radius=60 * s, fill=(110, 84, 50))
    img.alpha_composite(back.rotate(-9, center=(512 * s, 470 * s), resample=Image.BICUBIC))
    d.rounded_rectangle([212 * s, 300 * s, 812 * s, 790 * s], radius=64 * s, fill=(224, 164, 88))
    font = ImageFont.truetype(FONT, int(250 * s))
    d.text((512 * s, 520 * s), "103", font=font, fill=(30, 30, 30), anchor="mm")
    d.rounded_rectangle([352 * s, 668 * s, 672 * s, 692 * s], radius=12 * s, fill=(30, 30, 30))
    return img


def main():
    """Write <parent>/<name>.app: an AppleScript applet, so macOS asks once for access to the folder.

    It is built and signed in a temp folder: iCloud-synced folders add attributes that codesign rejects.
    """
    name = sys.argv[1] if len(sys.argv) > 1 else "AI-103 lernen"
    target = ROOT.parent / f"{name}.app"
    script = (f'do shell script quoted form of (POSIX path of (path to me) & "../{ROOT.name}/scripts/open_app.sh")'
              ' & " > /dev/null 2>&1 &"')
    with tempfile.TemporaryDirectory() as tmp:
        app = Path(tmp) / f"{name}.app"
        subprocess.run(["osacompile", "-o", str(app), "-e", script], check=True)
        plist_path = app / "Contents/Info.plist"
        plist = plistlib.loads(plist_path.read_bytes())
        plist.update({"CFBundleName": name, "CFBundleIdentifier": "local.vocab-trainer.launcher", "LSUIElement": True})
        plist_path.write_bytes(plistlib.dumps(plist))

        iconset = Path(tmp) / "AppIcon.iconset"
        iconset.mkdir()
        big = icon()
        for px in (16, 32, 128, 256, 512):
            big.resize((px, px), Image.LANCZOS).save(iconset / f"icon_{px}x{px}.png")
            big.resize((px * 2, px * 2), Image.LANCZOS).save(iconset / f"icon_{px}x{px}@2x.png")
        subprocess.run(["iconutil", "-c", "icns", str(iconset), "-o", str(app / "Contents/Resources/applet.icns")],
                       check=True)
        subprocess.run(["codesign", "--force", "--deep", "-s", "-", str(app)], check=True)
        shutil.rmtree(target, ignore_errors=True)
        subprocess.run(["ditto", str(app), str(target)], check=True)
    print(target)


if __name__ == "__main__":
    main()

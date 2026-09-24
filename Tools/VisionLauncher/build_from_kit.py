#!/usr/bin/env python3
"""Build a layered visionOS launcher IPA from a LiveContainer launcher kit."""

import argparse
import hashlib
import io
import json
import plistlib
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image


ROOT = Path(__file__).resolve().parent


def run(*args: str, cwd: Path) -> None:
    subprocess.run(args, cwd=cwd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kit", type=Path, help="Launcher kit ZIP exported by LiveContainer")
    parser.add_argument("--output", type=Path, default=Path.cwd() / "VisionLauncher.ipa")
    parser.add_argument("--simulator", action="store_true", help="Build for the visionOS simulator")
    parser.add_argument("--app-output", type=Path, help="Also copy the built .app to this path")
    args = parser.parse_args()

    with zipfile.ZipFile(args.kit) as archive:
        prefix = "LauncherKit/" if "LauncherKit/Launcher.json" in archive.namelist() else ""
        manifest = json.loads(archive.read(prefix + "Launcher.json"))
        icon_bytes = archive.read(prefix + "Icon.png")

    name = manifest["displayName"]
    launch_url = manifest["launchURL"]
    parsed = urlparse(launch_url)
    if not parsed.scheme.startswith("livecontainer") or parsed.netloc != "livecontainer-launch":
        raise ValueError("Kit launch URL must use a LiveContainer launcher scheme")
    suffix = hashlib.sha256(launch_url.encode()).hexdigest()[:20]
    bundle_id = f"dev.livecontainer.visionlauncher.{suffix}"

    with tempfile.TemporaryDirectory(prefix="vision-launcher-") as directory:
        work = Path(directory)
        shutil.copytree(ROOT / "Sources", work / "Sources")
        shutil.copytree(ROOT / "Assets.xcassets", work / "Assets.xcassets")
        shutil.copy2(ROOT / "project.yml", work / "project.yml")
        plist = plistlib.loads((ROOT / "Info.plist").read_bytes())
        plist["CFBundleDisplayName"] = name
        plist["LCLaunchURL"] = launch_url
        (work / "Info.plist").write_bytes(plistlib.dumps(plist))

        project = (work / "project.yml").read_text()
        project = project.replace("PRODUCT_BUNDLE_IDENTIFIER: dev.visionlauncher.youtube", f"PRODUCT_BUNDLE_IDENTIFIER: {bundle_id}")
        project = project.replace("CFBundleDisplayName: YouTube", f"CFBundleDisplayName: {json.dumps(name, ensure_ascii=False)}")
        project = project.replace(
            "LCLaunchURL: livecontainer://livecontainer-launch?bundle-name=com.google.ios.youtube123.app",
            f"LCLaunchURL: {json.dumps(launch_url)}",
        )
        (work / "project.yml").write_text(project)

        # Same structure as the hand-made YouTube launcher: the untouched guest
        # icon on the front layer over a solid back layer in the icon's own
        # background color. visionOS adds the depth, specular and shadow itself.
        original = Image.open(io.BytesIO(icon_bytes)).convert("RGBA").resize((1024, 1024), Image.LANCZOS)
        corners = [original.getpixel(p)[:3] for p in ((8, 8), (1015, 8), (8, 1015), (1015, 1015))]
        back_color = tuple(sorted(channel)[len(channel) // 2] for channel in zip(*corners))
        Image.new("RGB", (1024, 1024), back_color).save(
            work / "Assets.xcassets/AppIcon.solidimagestack/Back.solidimagestacklayer/Content.imageset/background.jpg",
            quality=95,
        )
        original.save(work / "Assets.xcassets/AppIcon.solidimagestack/Front.solidimagestacklayer/Content.imageset/youtube-icon.png")

        run("xcodegen", "generate", cwd=work)
        sdk = "xrsimulator" if args.simulator else "xros"
        destination = "generic/platform=visionOS Simulator" if args.simulator else "generic/platform=visionOS"
        run(
            "xcodebuild", "-project", "VisionLauncher.xcodeproj", "-scheme", "VisionLauncher",
            "-configuration", "Release", "-sdk", sdk, "-destination", destination,
            "-derivedDataPath", str(work / "DerivedData"), "CODE_SIGNING_ALLOWED=NO", "build", cwd=work,
        )
        app = work / f"DerivedData/Build/Products/Release-{sdk}/VisionLauncher.app"
        if not app.exists():
            raise FileNotFoundError(app)
        if args.app_output:
            app_output = args.app_output.resolve()
            if app_output.exists():
                shutil.rmtree(app_output)
            shutil.copytree(app, app_output)
        output = args.output.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
            for file in app.rglob("*"):
                if file.is_file():
                    archive.write(file, Path("Payload") / app.name / file.relative_to(app))
        print(f"Created unsigned launcher IPA: {output}")
        print(f"Bundle ID: {bundle_id}")
        print("Sign this IPA with the same sideloading tool used for LiveContainer before installing.")


if __name__ == "__main__":
    main()

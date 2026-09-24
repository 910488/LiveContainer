# VisionLauncher proof of concept

This is a small native visionOS app that opens a specific LiveContainer guest through
`livecontainer://livecontainer-launch`. It is a separate installed app, so visionOS
gives it its own Home View icon.

## Build a layered launcher from LiveContainer

In LiveContainer, hold a guest app and choose **Add to Home Screen → Export visionOS
launcher kit**. Save the ZIP to this Mac. The kit contains `Launcher.json` (display name
and launch URL) and `Icon.png`.

Run `python3 build_from_kit.py /path/to/VisionLauncher-kit.zip --output /path/to/Launcher.ipa`.
This requires Xcode, XcodeGen, and Pillow (`python3 -m pip install pillow`). The script
puts the untouched guest icon on the Front layer over a solid Back layer in the icon's own
background color (the same structure as the `YouTube` launcher), compiles them using Xcode,
and packages an
unsigned visionOS IPA. Sign and install the IPA using the same sideloading method as
LiveContainer. The exported IPA cannot be installed unsigned on a physical Vision Pro.

Each launch URL gets a stable launcher bundle identifier. Exporting the same guest and
container again updates the same launcher when signed consistently. A launcher's icon
only updates after rebuilding and reinstalling it.

This Mac build step is required for the icon's depth effect. LiveContainer cannot run
Xcode's visionOS asset compiler on the headset.

Do not crop, blur or add shadows to the icon layers. visionOS draws the depth,
specular highlight and shadow itself.

## Change the target

Edit `project.yml`:

- `PRODUCT_BUNDLE_IDENTIFIER`: unique identifier for this launcher.
- `CFBundleDisplayName`: name shown in Home View.
- `LCLaunchURL`: the full URL from LiveContainer's **Copy Launch URL** action.

Replace the PNG/JPEG files in `Assets.xcassets/AppIcon.solidimagestack` with
1024 × 1024 artwork. The Back layer must be fully opaque. Keep the two layers.

Run `xcodegen generate` after editing `project.yml`, then build in Xcode. For a real
Apple Vision Pro, choose a valid Apple development team and sign the app. This Mac
currently has no code signing identity and no connected Vision Pro, so only the
simulator build was installed and launched here.

Run `build_from_kit.py` without `--simulator` to create an unsigned visionOS
device IPA. It cannot be installed until a signing tool signs it for the target
device. This remains a proof of concept until device testing passes.

On first launch, visionOS may ask whether the launcher can open LiveContainer.
The guest's final launch still depends on LiveContainer working on the physical device.

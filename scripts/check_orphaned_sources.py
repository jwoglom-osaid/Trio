#!/usr/bin/env python3
"""Fail if a Swift source file on disk is missing from its Xcode target.

Trio.xcodeproj does not use Xcode 16 filesystem-synchronized groups, so every
source file needs four explicit project.pbxproj entries (PBXBuildFile,
PBXFileReference, a group child, and a PBXSourcesBuildPhase member). A commit
that adds a .swift file without touching the project file leaves it invisible
to the compiler, and the build fails far away from the cause with a pile of
"cannot find 'X' in scope" errors.

This runs in a second without Xcode, so CI can catch the omission before
paying for a 19-minute archive.
"""

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PBXPROJ = REPO / "Trio.xcodeproj" / "project.pbxproj"

# Source roots that build into the app or its test bundles, mapped to a label.
# Submodules and SwiftPM packages carry their own manifests and are excluded.
SOURCE_ROOTS = {
    "Trio/Sources": "Trio",
    "TrioTests": "TrioTests",
}

# Pre-existing dead files: present on disk, in no target, and referenced by
# nothing that builds. Baselined so the check fails only on NEW orphans.
# Deleting any of these is safe; drop it from this list when you do.
EXEMPT: set[str] = {
    # Superseded modules whose PBXGroup no longer exists in the project at all.
    "Trio/Sources/Modules/AddCarbs/AddCarbsStateModel.swift",
    "Trio/Sources/Modules/AddCarbs/View/AddCarbsRootView.swift",
    "Trio/Sources/Modules/AutotuneConfig/AutotuneConfigDataFlow.swift",
    "Trio/Sources/Modules/AutotuneConfig/AutotuneConfigProvider.swift",
    "Trio/Sources/Modules/AutotuneConfig/AutotuneConfigStateModel.swift",
    "Trio/Sources/Modules/AutotuneConfig/View/AutotuneConfigRootView.swift",
    "Trio/Sources/Modules/LibreConfig/View/LibreConfigRootView.swift",
    # Stale duplicate of LiveActitiyAttributes.swift (sic) — the misspelled
    # file is the one wired into the target and defining the live type.
    "Trio/Sources/Services/LiveActivity/LiveActivityAttributes.swift",
    # Unreferenced leftovers in groups that do still exist.
    "Trio/Sources/APS/OpenAPSSwift/AlgorithmLoggingShim.swift",
    "Trio/Sources/APS/OpenAPSSwift/Extensions/ComputedBGTargets+Getter.swift",
    "Trio/Sources/Helpers/SettingsRowView.swift",
    "Trio/Sources/Modules/Settings/View/SettingsRootViewModel.swift",
    "Trio/Sources/Modules/Stat/View/ChartsView.swift",
    "TrioTests/CGMManagerAlertOwnershipTests.swift",
    "TrioTests/SettingsExportTests.swift",
}


def build_phase_members(text: str) -> set[str]:
    """Every build-file UUID referenced by any PBXSourcesBuildPhase."""
    members: set[str] = set()
    section = re.search(
        r"/\* Begin PBXSourcesBuildPhase section \*/(.*?)"
        r"/\* End PBXSourcesBuildPhase section \*/",
        text,
        re.S,
    )
    if not section:
        sys.exit("error: no PBXSourcesBuildPhase section found in project.pbxproj")
    for uuid in re.finditer(r"^\s*([0-9A-Za-z]{24}) /\* .* in Sources \*/,", section.group(1), re.M):
        members.add(uuid.group(1))
    return members


def compiled_filenames(text: str) -> set[str]:
    """Basenames of files reachable from a Sources build phase."""
    members = build_phase_members(text)

    # PBXBuildFile: <buildUUID> /* Name in Sources */ = {... fileRef = <refUUID> ...}
    build_files = {}
    for m in re.finditer(
        r"^\s*([0-9A-Za-z]{24}) /\* (.+?) in Sources \*/ = \{isa = PBXBuildFile;"
        r"(?:.*?)fileRef = ([0-9A-Za-z]{24})",
        text,
        re.M,
    ):
        build_files[m.group(1)] = (m.group(2), m.group(3))

    # A file counts as compiled only if its PBXBuildFile is actually listed in a
    # Sources phase — an orphaned PBXBuildFile still builds nothing.
    return {name for uuid, (name, _ref) in build_files.items() if uuid in members}


def main() -> int:
    text = PBXPROJ.read_text()
    compiled = compiled_filenames(text)

    missing: list[str] = []
    for root, label in SOURCE_ROOTS.items():
        for path in sorted((REPO / root).rglob("*.swift")):
            rel = path.relative_to(REPO).as_posix()
            if rel in EXEMPT:
                continue
            if path.name not in compiled:
                missing.append(f"{rel}  (target: {label})")

    if missing:
        print("error: Swift files on disk are not compiled by any target:\n")
        for entry in missing:
            print(f"  {entry}")
        print(
            "\nAdd each file to its target in Xcode (or add the four "
            "project.pbxproj entries by hand):\n"
            "  1. PBXBuildFile        2. PBXFileReference\n"
            "  3. PBXGroup child      4. PBXSourcesBuildPhase member"
        )
        return 1

    total = sum(len(list((REPO / root).rglob("*.swift"))) for root in SOURCE_ROOTS)
    print(f"ok: all {total} Swift files under {', '.join(SOURCE_ROOTS)} are wired into a target")
    return 0


if __name__ == "__main__":
    sys.exit(main())

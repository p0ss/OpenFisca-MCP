#!/usr/bin/env python3
"""Give a vendored country package an explicit, honest dependency contract.

Usage: relock-country-package.py COUNTRY_DIR API_LOCK LOCAL_TAG

Country packages usually declare ``openfisca-core[web-api] >=X, <Y``. Two
problems follow for a patched runtime: the ceiling can exclude the Core release
the image ships, and the ``web-api`` extra pins a Flask-CORS range that excludes
security fixes. Rather than bypass ``pip check``, this rewrites only the
package's declared dependencies to the exact versions in the API lock and
marks the result with a PEP 440 local version (``22.0.0+LOCAL_TAG``), so the
installed metadata states plainly that this is a repackaged build.

Calculation code, parameters and tests are not touched. The script refuses to
run if the upstream declaration is not the single, recognised Core requirement,
so an upstream change forces a review instead of being silently rewritten.
"""
import re
import sys
from pathlib import Path

WEB_DEPENDENCIES = ("Flask", "Flask-Cors", "gunicorn", "Werkzeug")
CORE_REQUIREMENT = re.compile(r'^\s*"openfisca-core(\[web-api\])?\s*[^"]*",\s*$', re.IGNORECASE)


def locked_versions(lock_path: Path) -> dict[str, str]:
    versions = {}
    for line in lock_path.read_text().splitlines():
        match = re.match(r"^([A-Za-z0-9._-]+)==([^\s\\]+)", line)
        if match:
            versions[match.group(1).lower().replace("_", "-")] = match.group(2)
    return versions


def main() -> int:
    country_dir, lock_path, local_tag = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
    if not re.fullmatch(r"[A-Za-z0-9.]+", local_tag):
        raise SystemExit(f"invalid local version tag: {local_tag!r}")
    versions = locked_versions(lock_path)
    pyproject = country_dir / "pyproject.toml"
    lines = pyproject.read_text().splitlines(keepends=True)

    core_lines = [i for i, line in enumerate(lines) if CORE_REQUIREMENT.match(line)]
    if len(core_lines) != 1:
        raise SystemExit(f"{pyproject}: expected exactly one openfisca-core requirement, found {len(core_lines)}; review required")
    indent = re.match(r"^\s*", lines[core_lines[0]]).group(0)
    pins = ["OpenFisca-Core", *WEB_DEPENDENCIES]
    replacement = "".join(f'{indent}"{name}=={versions[name.lower()]}",\n' for name in pins)
    lines[core_lines[0]] = replacement

    text = "".join(lines)
    version = re.search(r'^version\s*=\s*"([^"+]+)"', text, re.MULTILINE)
    if not version:
        raise SystemExit(f"{pyproject}: no static version; review required")
    text = text.replace(version.group(0), f'version = "{version.group(1)}+{local_tag}"', 1)
    pyproject.write_text(text)
    print(f"{country_dir.name} {version.group(1)}+{local_tag}: " + ", ".join(f"{n}=={versions[n.lower()]}" for n in pins))
    return 0


if __name__ == "__main__":
    sys.exit(main())

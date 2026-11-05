"""Check the installed library API before the app accepts calculations."""

import inspect
import ntpath
import os
import re
import shlex
import sys
from importlib.metadata import PackageNotFoundError, version

import marksgeometrys


class DependencyCompatibilityError(RuntimeError):
    """The active Python cannot provide the marksgeometrys API used by the UI."""


_VERSION_PATTERN = re.compile(
    r"^\s*v?(?:(?P<epoch>\d+)!)?(?P<release>\d+(?:\.\d+)*)"
    r"(?P<pre>[-_.]?(?:alpha|beta|preview|pre|rc|a|b|c)[-_.]?\d*)?"
    r"(?P<post>-\d+|[-_.]?(?:post|rev|r)[-_.]?\d*)?"
    r"(?P<dev>[-_.]?dev[-_.]?\d*)?"
    r"(?:\+[a-z0-9]+(?:[-_.][a-z0-9]+)*)?\s*$",
    re.IGNORECASE,
)


def _supports_required_release(installed_version: str) -> bool:
    match = _VERSION_PATTERN.fullmatch(installed_version)
    if match is None:
        return False
    if int(match.group("epoch") or 0):
        return True
    release = tuple(int(part) for part in match.group("release").split("."))
    release = release + (0,) * max(0, 2 - len(release))
    minimum = (0, 2) + (0,) * max(0, len(release) - 2)
    if release != minimum:
        return release > minimum
    return not match.group("pre") and not (
        match.group("dev") and not match.group("post")
    )


def _powershell_quote(value: str) -> str:
    return '"' + value.replace("`", "``").replace("$", "`$").replace('"', '`"') + '"'


def _upgrade_command() -> str:
    executable = sys.executable
    if os.name == "nt":
        # A desktop shortcut can run pythonw.exe; use its console companion for pip.
        if ntpath.basename(executable).lower() == "pythonw.exe":
            executable = ntpath.join(ntpath.dirname(executable), "python.exe")
        return "& " + _powershell_quote(executable) + (
            ' -m pip install --upgrade "marksgeometrys>=0.2"'
        )
    return shlex.join([executable, "-m", "pip", "install", "--upgrade", "marksgeometrys>=0.2"])


def _incompatibility(installed_version: str, reason: str) -> DependencyCompatibilityError:
    return DependencyCompatibilityError(
        "marksgeometrys 0.2 or later is required for unit-aware, numeric calculations.\n"
        + "Installed version: " + installed_version + "\n"
        + "Compatibility problem: " + reason + "\n"
        + "Python executable: " + sys.executable + "\n"
        + "Loaded library: " + str(getattr(marksgeometrys, "__file__", "unknown")) + "\n\n"
        + "Upgrade this Python installation with:\n" + _upgrade_command() + "\n\n"
        + "Restart the app after upgrading so it loads the updated library."
    )


def ensure_library_compatible() -> None:
    """Require the numeric 0.2 API and unit keyword without executing geometry.

    Check the loaded classes as well as distribution metadata: an old module can
    remain loaded after pip upgrades an installation. Actual result types are
    still validated when the app calls the library's measurement methods.
    """
    try:
        installed_version = version("marksgeometrys")
    except PackageNotFoundError:
        raise _incompatibility("unknown", "Package version metadata is missing.") from None
    if not _supports_required_release(installed_version):
        raise _incompatibility(installed_version, "The installed release predates the required API.")

    for class_name in ("Circle", "Rectangle", "Sphere"):
        constructor = getattr(marksgeometrys, class_name, None)
        if not callable(constructor):
            raise _incompatibility(installed_version, class_name + " is missing or is not callable.")
        try:
            inspect.signature(constructor).bind_partial(unit="cm")
        except (TypeError, ValueError):
            raise _incompatibility(
                installed_version, class_name + " does not support the unit keyword.",
            ) from None
        method_name = "volume" if class_name == "Sphere" else "area"
        if not callable(getattr(constructor, method_name, None)):
            raise _incompatibility(
                installed_version, class_name + "." + method_name + "() is unavailable.",
            )

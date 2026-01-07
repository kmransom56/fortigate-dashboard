"""Shim: ssl_universal_fix_v2 relocated.

This root-level shim exists so that executing Python from the repository
root (Utilities/) can still ``import ssl_universal_fix_v2`` even though the
former file now lives inside the subproject and functionality was merged
into the canonical module ``ssl_tools.ssl_universal_fix``.

Preferred import going forward:
    from ssl_tools import ssl_universal_fix

Removal target: after 2025-10-01 (or later if still referenced).
"""
import os as _os, sys as _sys  # minimal local bootstrap
_root = _os.path.dirname(__file__)
_candidate = _os.path.join(_root, 'cisco-meraki-cli')
if _candidate not in _sys.path and _os.path.isdir(_os.path.join(_candidate, 'ssl_tools')):
    _sys.path.insert(0, _candidate)
import warnings as _warnings
if not globals().get('_SSL_V2_ROOT_SHIM_WARNED'):
    _warnings.warn(
        "Root shim 'ssl_universal_fix_v2' is deprecated; use 'from ssl_tools import ssl_universal_fix'",
        DeprecationWarning,
        stacklevel=2,
    )
    _SSL_V2_ROOT_SHIM_WARNED = True

try:  # final import
    from ssl_tools.ssl_universal_fix import *  # type: ignore  # noqa: F401,F403
except ModuleNotFoundError as _e:  # pragma: no cover
    raise ModuleNotFoundError(
        "ssl_tools package not found. Run from repository root or ensure 'cisco-meraki-cli' is on PYTHONPATH"
    ) from _e

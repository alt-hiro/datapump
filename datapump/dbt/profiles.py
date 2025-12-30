"""Utilities for loading dbt profiles."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Any

import yaml


class ProfileError(Exception):
    """Raised when a dbt profile cannot be resolved."""


@dataclass(frozen=True)
class TargetProfile:
    profile_name: str
    target_name: str
    adapter_type: str
    config: dict[str, Any]


def _default_profiles_path() -> Path:
    profiles_dir = os.environ.get("DBT_PROFILES_DIR", os.path.expanduser("~/.dbt"))
    return Path(profiles_dir) / "profiles.yml"


def _load_profiles(profiles_path: Path) -> dict[str, Any]:
    if not profiles_path.exists():
        raise ProfileError(f"profiles.yml not found at {profiles_path}")
    with profiles_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ProfileError("profiles.yml must contain a mapping of profiles")
    return data


def _resolve_profile_name(profiles: dict[str, Any], profile_name: str | None) -> str:
    if profile_name:
        if profile_name not in profiles:
            raise ProfileError(f"profile '{profile_name}' not found in profiles.yml")
        return profile_name
    env_profile = os.environ.get("DBT_PROFILE")
    if env_profile:
        if env_profile not in profiles:
            raise ProfileError(f"profile '{env_profile}' not found in profiles.yml")
        return env_profile
    if len(profiles) == 1:
        return next(iter(profiles))
    raise ProfileError("profile name required when multiple profiles are defined")


def _resolve_target_name(profile: dict[str, Any], target_name: str | None) -> str:
    outputs = profile.get("outputs", {})
    if not isinstance(outputs, dict):
        raise ProfileError("profile outputs must be a mapping")
    if target_name:
        if target_name not in outputs:
            raise ProfileError(f"target '{target_name}' not found in profile outputs")
        return target_name
    default_target = profile.get("target")
    if default_target:
        if default_target not in outputs:
            raise ProfileError(
                f"default target '{default_target}' not found in profile outputs"
            )
        return default_target
    if len(outputs) == 1:
        return next(iter(outputs))
    raise ProfileError("target name required when multiple outputs are defined")


def load_target_profile(
    *,
    profile_name: str | None = None,
    target_name: str | None = None,
    profiles_path: str | Path | None = None,
) -> TargetProfile:
    """Load a dbt profile and return the selected target configuration."""

    path = Path(profiles_path) if profiles_path else _default_profiles_path()
    profiles = _load_profiles(path)
    resolved_profile_name = _resolve_profile_name(profiles, profile_name)
    profile = profiles[resolved_profile_name]
    if not isinstance(profile, dict):
        raise ProfileError("profile definition must be a mapping")
    resolved_target_name = _resolve_target_name(profile, target_name)
    outputs = profile.get("outputs", {})
    target_config = outputs.get(resolved_target_name, {})
    if not isinstance(target_config, dict):
        raise ProfileError("target configuration must be a mapping")
    adapter_type = target_config.get("type")
    if not adapter_type:
        raise ProfileError("target configuration missing adapter type")
    return TargetProfile(
        profile_name=resolved_profile_name,
        target_name=resolved_target_name,
        adapter_type=str(adapter_type),
        config=target_config,
    )

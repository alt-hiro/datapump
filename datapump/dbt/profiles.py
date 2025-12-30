import pathlib
from typing import Any, Dict

import yaml


def _default_profiles_dir(project_dir: pathlib.Path) -> pathlib.Path:
    return pathlib.Path.home() / ".dbt"


def load_profile(
    project_dir: pathlib.Path,
    profiles_dir: str | None,
    profile_name: str | None,
    target_name: str | None,
) -> Dict[str, Any]:
    profiles_path = pathlib.Path(profiles_dir) if profiles_dir else _default_profiles_dir(project_dir)
    profiles_file = profiles_path / "profiles.yml"
    if not profiles_file.exists():
        raise FileNotFoundError(f"profiles.yml not found at {profiles_file}")

    with open(profiles_file, "r", encoding="utf-8") as handle:
        profiles = yaml.safe_load(handle) or {}

    if not profile_name:
        profile_name = _infer_profile_name(project_dir, profiles)
    profile = profiles.get(profile_name)
    if not profile:
        raise ValueError(f"Profile {profile_name} not found in {profiles_file}")

    target = target_name or profile.get("target")
    outputs = profile.get("outputs", {})
    target_profile = outputs.get(target)
    if not target_profile:
        raise ValueError(f"Target {target} not found in profile {profile_name}")

    return target_profile


def _infer_profile_name(project_dir: pathlib.Path, profiles: Dict[str, Any]) -> str:
    project_file = project_dir / "dbt_project.yml"
    if project_file.exists():
        with open(project_file, "r", encoding="utf-8") as handle:
            project = yaml.safe_load(handle) or {}
        profile = project.get("profile")
        if profile:
            return profile

    if len(profiles) == 1:
        return next(iter(profiles.keys()))

    raise ValueError("Profile name not provided and could not be inferred")

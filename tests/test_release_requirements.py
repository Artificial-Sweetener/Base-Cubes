"""Protect published cube versions and their installable node-pack requirements."""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from sugarcubes.backend.services.dependency_requirements import (
    extract_versioned_requirements,
)
from sugarcubes.backend.services.dependency_version_types import InstalledDependency
from sugarcubes.backend.services.dependency_versions import (
    build_dependency_version_plan,
)
from sugarcubes.cube_model import CubeDocument

PACK = Path(__file__).resolve().parents[1]
LATEST_SIMPLE_SYRUP = "1.14.1"
CUBES = tuple(sorted(PACK.glob("*/*.cube")))


def simple_syrup_properties(value: object) -> Iterator[dict[str, Any]]:
    """Find persisted version declarations across canonical and nested graphs."""
    if isinstance(value, dict):
        if value.get("cnr_id") == "SimpleSyrup":
            yield value
        for child in value.values():
            yield from simple_syrup_properties(child)
    elif isinstance(value, list):
        for child in value:
            yield from simple_syrup_properties(child)


@pytest.mark.parametrize(
    "path", CUBES, ids=lambda path: path.relative_to(PACK).as_posix()
)
def test_every_cube_requires_the_published_simple_syrup(path: Path) -> None:
    """Make dependency repair request the release even for the core image loader."""
    payload: Any = json.loads(path.read_text(encoding="utf-8"))
    document = CubeDocument.from_dict(payload)
    assert CubeDocument.from_dict(document.to_dict()) == document
    declarations = tuple(simple_syrup_properties(payload))
    assert declarations
    assert {entry["ver"] for entry in declarations} == {LATEST_SIMPLE_SYRUP}
    requirements = extract_versioned_requirements(
        document.to_dict(),
        cube_id=document.cube_id,
        pack_ref="Artificial-Sweetener/Base-Cubes",
        source_path=str(path),
        default_base_repo=True,
    )
    simple_syrup = tuple(item for item in requirements if item.node_id == "SimpleSyrup")
    assert not any(
        item.node_id == "SugarCubes" and item.required_version == "0.15.3"
        for item in requirements
    )
    assert simple_syrup
    assert {item.required_version for item in simple_syrup} == {LATEST_SIMPLE_SYRUP}
    assert all(item.version_policy == "minimum" for item in simple_syrup)
    for installed_version, expected_status in (
        ("1.13.0", "installed_version_too_old"),
        (LATEST_SIMPLE_SYRUP, "satisfied"),
    ):
        installed = InstalledDependency(
            folder_name="SimpleSyrup",
            source_path="custom_nodes/SimpleSyrup",
            installed_version=installed_version,
            version_kind="semver",
            source_kind="git",
            repository_url="https://github.com/Artificial-Sweetener/SimpleSyrup",
            dirty=False,
        )
        plan = build_dependency_version_plan(
            grouped_requirements={"simplesyrup": simple_syrup},
            installed_by_key={"simplesyrup": installed},
            git_contains=lambda _source, _head, _required: False,
        )
        assert plan[0]["requiredVersion"] == LATEST_SIMPLE_SYRUP
        assert plan[0]["status"] == expected_status
        assert plan[0]["repairable"] is (expected_status != "satisfied")


@pytest.mark.parametrize("family", ("Anima", "Krea 2"))
def test_latent_cubes_require_only_simple_syrup_and_use_plain_sampler_names(
    family: str,
) -> None:
    """Keep cube dependencies scoped to SimpleSyrup and use plain sampler names."""
    path = PACK / family / "Latent Upscale.cube"
    payload: Any = json.loads(path.read_text(encoding="utf-8"))
    document = CubeDocument.from_dict(payload)
    requirements = extract_versioned_requirements(
        document.to_dict(),
        cube_id=document.cube_id,
        pack_ref="Artificial-Sweetener/Base-Cubes",
        source_path=str(path),
        default_base_repo=True,
    )
    assert {item.node_id for item in requirements} == {"SimpleSyrup"}
    implementation = payload["implementation"]
    assert implementation["nodes"]["ksampler"]["label"] == "KSampler"
    assert implementation["layout"]["nodes"]["ksampler"]["title"] == "KSampler"
    assert (
        implementation["definitions"]["SimpleSyrup.KSampler"]["display_name"]
        == "KSampler"
    )
    assert "Contextual Attention" not in json.dumps(implementation["definitions"])
    assert document.version == "1.0.2"


def test_existing_cube_versions_advance_for_the_release() -> None:
    """Require new patch versions for the existing catalog dependency changes."""
    expected = {
        "Anima/Automask Detailer.cube": "3.1.2",
        "Anima/Contextual Upscale.cube": "1.1.2",
        "Anima/Diffusion Upscale.cube": "5.1.2",
        "Anima/Image to Image.cube": "3.1.2",
        "Anima/Inpaint.cube": "3.1.2",
        "Anima/Prompt by Region.cube": "5.1.2",
        "Anima/Promptmask Detailer.cube": "3.1.2",
        "Anima/Text to Image.cube": "3.1.2",
        "Anima/TileRegion Upscale.cube": "3.1.2",
        "Any/Load Image.cube": "2.0.3",
        "Flux2 Klein/Edit by Prompt.cube": "2.1.2",
        "Krea 2/Contextual Upscale.cube": "2.2.2",
        "Krea 2/Text to Image.cube": "2.2.2",
        "SDXL/Automask Detailer.cube": "4.1.2",
        "SDXL/Diffusion Upscale.cube": "5.1.2",
        "SDXL/Image to Image.cube": "3.1.2",
        "SDXL/Inpaint.cube": "3.1.2",
        "SDXL/Prompt by Region.cube": "2.1.2",
        "SDXL/Promptmask Detailer.cube": "3.1.2",
        "SDXL/Text to Image.cube": "3.1.2",
        "SDXL/Tiled Diffusion Upscale.cube": "2.1.2",
        "SeedVR2/Diffusion Upscale.cube": "2.1.2",
    }
    actual = {
        path.relative_to(PACK).as_posix(): json.loads(path.read_text())["version"]
        for path in CUBES
        if path.name != "Latent Upscale.cube"
    }
    assert actual == expected

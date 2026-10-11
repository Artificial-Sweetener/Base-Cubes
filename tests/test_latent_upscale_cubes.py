"""Protect the latent-only, source-noise CD contract of the model family Cubes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from sugarcubes.cube_model import CubeDocument
from sugarcubes.cube_model.merge import materialize_nodes
from sugarcubes.execution.cube_document_lowering import CubeDocumentLowerer
from sugarcubes.importer import load_cube_document, prepare_import

PACK = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "family,scale,steps,denoise,decay",
    [
        ("Anima", 1.5, 12, 0.15, 0.5),
        ("Krea 2", 1.5, 4, 0.25, 0.25),
    ],
)
def test_connected_latent_upscale_retains_noise_and_regional_sampling_contract(
    family: str,
    scale: float,
    steps: int,
    denoise: float,
    decay: float,
) -> None:
    """Require learned latent enlargement, capture reuse, and compatible region inputs."""
    payload: Any = json.loads(
        (PACK / family / "Latent Upscale.cube").read_text(encoding="utf-8")
    )
    document = CubeDocument.from_dict(payload)
    assert (
        document.cube_id
        == f"Artificial-Sweetener/Base-Cubes/{family}/Latent Upscale.cube"
    )
    assert document.metadata["default_alias"] == f"{family}/Latent Upscale"
    assert CubeDocument.from_dict(document.to_dict()) == document
    prepared = prepare_import(load_cube_document(document))
    assert prepared.warnings == []
    nodes = materialize_nodes(document)
    assert nodes["source_latent"]["class_type"] == "SimpleSyrup.LatentFromImage"
    assert nodes["source_latent"]["inputs"]["image"] == ["@binding", "input.image"]
    assert nodes["latent_upscale"]["inputs"] == {
        "latent": ["source_latent", 0],
        "method": "Auto",
        "scale_factor": scale,
    }
    assert nodes["noise_reuse"]["inputs"]["enabled"] is True
    assert nodes["noise_reuse"]["inputs"]["finishing_steps"] == 0
    assert nodes["noise_reuse"]["inputs"]["options"] == ["contextual_diffusion", 0]
    assert nodes["attention_coupling"]["inputs"]["options"] == ["noise_reuse", 0]
    assert nodes["attention_coupling"]["mode"] == 4
    sampler = nodes["ksampler"]
    assert sampler["class_type"] == "SimpleSyrup.KSampler"
    assert sampler["inputs"]["latent_image"] == ["latent_upscale", 0]
    assert sampler["inputs"]["options"] == ["attention_coupling", 0]
    assert sampler["inputs"]["region_masks"] == ["@binding", "input.mask"]
    assert (sampler["inputs"]["steps"], sampler["inputs"]["denoise"]) == (
        steps,
        denoise,
    )
    assert nodes["contextual_diffusion"]["inputs"]["global_decay"] == decay
    assert nodes["contextual_diffusion"]["inputs"]["latent_context_size"] == 128
    assert nodes["models"]["mode"] == 4
    assert document.implementation.outputs == {"output.image": ["vae_decode", 0]}
    assert not any(
        "VAEEncode" in node["class_type"]
        or "ContextualAttention" in node["class_type"]
        or "NoiseInversion" in node["class_type"]
        for node in nodes.values()
    )
    controls = {control.control_id for control in document.surface.controls}
    assert set(document.flavors.authored[0].values) == controls
    assert "attention_coupling.regional_prompt_weight" in controls
    assert "attention_coupling.region_mask_feather" in controls
    lowered = CubeDocumentLowerer().lower("upscale", document)
    assert "upscale:attention_coupling" not in lowered.prompt
    lowered_inputs = lowered.prompt["upscale:ksampler"]["inputs"]
    assert isinstance(lowered_inputs, dict)
    assert lowered_inputs["options"] == ["upscale:noise_reuse", 0]

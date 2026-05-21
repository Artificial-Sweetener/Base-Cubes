# Base-Cubes

**Base-Cubes** is the default SugarCubes pack for reusable ComfyUI image workflows.

It gives you ready-made `.cube` workflow units for the things image builders do constantly: generating images, transforming images, inpainting, upscaling, detailing, masking, and loading images into a larger graph.

The cubes are stored by target model family, so you will see names like `SDXL/Text to Image` or `Anima/Diffusion Upscale` inside SugarCubes. That name tells you which implementation you are using. The more useful way to think about the pack, though, is by what each cube does.

## The Cubes

Base-Cubes is a small kit of workflow building blocks. Some cubes exist for more than one model type, and some are specialized because the underlying model or node stack needs a different approach.

### Generation

**Text to Image**  
Supported model types: **SDXL**, **Anima**

Generate an image from prompts and model settings. These cubes handle the normal generation path: model loading, positive and negative prompts, prompt scheduling, LoRA scheduling, sampling, and VAE decoding.

The SDXL version includes checkpoint and VAE controls, prompt encode style selection, Mahiro positive-biased guidance, and VectorscopeCC color controls.

The Anima version uses the Anima model loader and keeps the prompt and LoRA scheduling path suited to Anima workflows.

### Image Transformation

**Image to Image**  
Supported model types: **SDXL**, **SD 1.5**

Transform an existing image with diffusion. This is the standard img2img shape: load an image, encode it, condition it with prompts, sample with denoise control, and decode the result.

Use it when the source image should remain part of the final result, but you want diffusion to reinterpret, restyle, or repair it.

### Inpainting

**Inpaint**  
Supported model types: **SDXL**, **SD 1.5**

Rebuild masked regions of an image while preserving the surrounding context. The cube loads an image and mask, applies inpaint conditioning, and runs diffusion with prompt, checkpoint, VAE, denoise, and color controls.

Use it when the edit area is explicit: replacing an object, repairing a hand, changing clothing, extending a detail, or cleaning up a localized artifact.

### Upscaling

**Diffusion Upscale**  
Supported model types: **SDXL**, **Anima**, **SeedVR2**

Upscale an image, then use model-specific refinement to recover detail.

The SDXL version follows a hires-fix style path: upscale the input image, resize toward target constraints, encode it, and refine it through img2img diffusion.

The Anima version is tiled because Anima does not behave well when diffusion is run outside its supported resolutions. It upscales the image, then refines it in latent tiles so the diffusion work stays inside a safer resolution range.

The SeedVR2 version is a dedicated SeedVR2 upscaler. It loads the SeedVR2 DiT model and upscales an input image by a scale factor using the SeedVR2 node stack.

**Tile Region Upscale**  
Supported model types: **Anima**

Split an image into regions, tag those regions, and apply prompt-aware regional detailing.

This is a second Anima upscaling strategy for the same underlying limitation: getting larger Anima outputs without asking the model to diffuse the whole large image at once. Instead of tiled latent diffusion over the full image, this cube works region by region with WD14 tagging and regional prompt context.

### Detailing

**Automask Detailer**  
Supported model types: **SDXL**, **Anima**

Detect regions automatically, then refine those regions with diffusion.

These cubes use an Ultralytics detector to find regions in the input image, then pass those regions into a detailer. They are useful for ADetailer-style workflows where you want faces, bodies, hands, or other detected subjects to receive focused refinement.

The SDXL version uses the checkpoint path with prompt scheduling, Mahiro guidance, VectorscopeCC controls, and scale-factor detailing.

The Anima version uses the Anima model loader and tiled diffusion detailer so detected regions can be refined without running Anima diffusion outside its supported resolutions.

**Promptmask Detailer**  
Supported model types: **SDXL**, **SD 1.5**, **Anima**

Create masks from text prompts, then refine the selected regions with diffusion.

These cubes use GroundingDINO, SAM, and ViTMatte to create prompt-guided masks. Instead of relying on a fixed detector class, you describe what should be selected, then the cube details those regions.

Use this when the target region is semantic: "eyes", "hair", "jewelry", "background flowers", "the red dress", or anything else that is easier to describe than detect with a fixed model.

The SDXL version uses checkpoint loading, prompt encoding, Mahiro guidance, color controls, and scale-factor detailing.

The Anima version uses Anima model loading and tiled diffusion detailing for the selected regions.

### Utility

**Load Image**  
Supported model types: **All**

Load an image for downstream SugarCubes or normal ComfyUI nodes.

This cube is intentionally simple. It gives workflows a reusable image source without tying the image load step to a specific model family.

## Supported Workflows

| Workflow | SDXL | SD 1.5 | Anima | SeedVR2 | Any |
| --- | --- | --- | --- | --- | --- |
| Text to Image | Yes |  | Yes |  |  |
| Image to Image | Yes | Yes |  |  |  |
| Inpaint | Yes | Yes |  |  |  |
| Diffusion Upscale | Yes |  | Yes | Yes |  |
| Tile Region Upscale |  |  | Yes |  |  |
| Automask Detailer | Yes |  | Yes |  |  |
| Promptmask Detailer | Yes | Yes | Yes |  |  |
| Load Image |  |  |  |  | Yes |

## Model Types

Base-Cubes keeps model-specific implementations separate because the best workflow shape is not identical across models.

**SDXL** cubes use checkpoint and VAE loading, prompt encode style controls, LoRA scheduling, Mahiro guidance, and VectorscopeCC color controls where appropriate.

**SD 1.5** support is available in compatible checkpoint-based workflows that do not depend on SDXL-only behavior.

**Anima** cubes use the Anima loader and expose Anima-oriented model controls. Upscaling and detailing workflows use tiled or region-based diffusion because Anima does not behave well when asked to diffuse outside its supported resolutions.

**SeedVR2** cubes are specialized for SeedVR2 upscaling. They use SeedVR2 model loading and scaling controls rather than a diffusion img2img refinement path.

**Any** cubes are model-neutral utilities. They are meant to feed other cubes or ordinary ComfyUI nodes.

## Using the Pack

SugarCubes-compatible tools load this repository as a cube library. Each `.cube` file is a serialized, validated workflow unit with stable bindings and embedded node definitions.

Inside the UI, cubes display with their model family in the name, such as `SDXL/Text to Image` or `Anima/Text to Image`. That naming is deliberate: it keeps the implementation clear while still letting you think in terms of the workflow you want to build.

Use the model-specific cube when you know which model family should do the work. Use `Any/Load Image` when you just need to bring an image into the graph before passing it into another cube.

## Included Files

- `SDXL/Text to Image.cube`
- `SDXL/Image to Image.cube`
- `SDXL/Inpaint.cube`
- `SDXL/Diffusion Upscale.cube`
- `SDXL/Automask Detailer.cube`
- `SDXL/Promptmask Detailer.cube`
- `Anima/Text to Image.cube`
- `Anima/Diffusion Upscale.cube`
- `Anima/Automask Detailer.cube`
- `Anima/Promptmask Detailer.cube`
- `Anima/TileRegion Upscale.cube`
- `SeedVR2/Diffusion Upscale.cube`
- `Any/Load Image.cube`

## License

Base-Cubes is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**.

Please read the full [LICENSE](LICENSE) included with this repo. The AGPL-3.0 is a strong copyleft license. If you distribute Base-Cubes or a modified version, you must provide the corresponding source; and if you let users interact with a modified version over a network, you must offer those users the corresponding source for that modified version.

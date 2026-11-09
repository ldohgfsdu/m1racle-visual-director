# Source-bound image edit (experimental)
This runner makes a real POST to OpenAI's `/v1/images/edits` with the **two input files' actual bytes** as base64 data URIs in `images[0]` (content) and `images[1]` (style). It is distinct from `scripts/prompt_builder.py`, which builds prompts only.

## Guangzhou I01 reproducible invocation

```bash
export OPENAI_API_KEY="<your key, set locally; never commit it>"
python scripts/run_source_bound_edit.py \
  --source /private/agriculture-or-guangzhou/guangzhou_original.jpg \
  --style-image assets/examples/I01_blue_coastal_architecture.jpg \
  --output /private/reviews/I01_guangzhou.png \
  --size 1152x1536 \
  --prompt "I01 precision banknote-style engraving. Deep blue ink, pale paper, continuous guilloche in unobstructed sky. Preserve the Guangzhou canal, Canton Tower, pedestrians, wires, facades, reflections and all original photograph labels."
```

`--dry-run` verifies the input bytes, dimensions, model choice and source/style roles without a network call, an API key, an output file, or an image-generation claim.

The default model `gpt-image-2.5-sunburst` is deliberately used because `gpt-image-1` was retired in October 2026 and GPT Image 2.5 supports arbitrary multiples-of-16 resolutions (subject to model limits). This content source is 1152×1536 (3:4); the reference image is 1536×869. The protocol uses the official JSON input form, `images: [{image_url: data:...}, ...]`, available for `/images/edits` (https://developers.openai.com/api/reference/resources/images/methods/edit).

The tool fails closed when: an image file is missing or invalid; source and style are the same file; the desired ratio deviates more than 1% from the source; the model returns something other than one PNG at the requested dimensions; there is no API key; or the destination already exists. It does not silently crop/stretch, write a substitute filter, or infer visual quality. It records a separate `*.provenance.json` containing file hashes, roles, request body hash, server request ID (when provided), and output dimensions, but not raw source images or the API key.

**Security and provenance limits:** A receipt proves what the local client serialized and reports the response; it is not cryptographic attestation of what the remote model actually attended to. The `source_binding` field is only `documented` when an API request ID is returned and still requires human review of the request trail. Every new image is `GENERATED_UNREVIEWED` by default. Human inspection must still check objects, fine engraving, original labels, and unwanted reports/infographics before PASS. Unit tests mock the HTTP service and DO NOT prove model quality or live API availability. This runner has not performed a live paid model invocation in the current chat environment due to missing `OPENAI_API_KEY`.

No original user photo or output belongs in the public GitHub repository; store user images and evidence in a private directory.

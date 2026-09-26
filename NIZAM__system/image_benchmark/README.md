# NIZAM Image Production Benchmark Harness

Purpose: compare image-edit production paths without allowing a producing model to grade itself.

## Safety defaults
- Paid calls are disabled by default.
- Originals are immutable.
- Producer names/models are hidden from evaluators.
- Missing metrics are never imputed.
- Identity failure, major unrequested change, or gross artifact fails the candidate regardless of weighted score.
- P0 ChatGPT subscription outputs are imported manually; a ChatGPT subscription is not treated as API entitlement.

## Evaluation layers
1. Objective/perceptual metrics: masked SSIM/LPIPS where masks exist; DINO/DreamSim-style similarity only on regions expected to remain unchanged; no-reference IQA is auxiliary only.
2. At least two independent multimodal judges using original + instruction + candidate + reference pack.
3. Blind pairwise A/B comparisons.
4. Human ACCEPT / MODIFY / RETRY / REJECT.

## Rubric
- identity_subject_preservation: 20
- photorealism_natural_texture: 15
- requested_edit_accuracy: 15
- edit_locality_unrequested_changes: 15
- reference_realism_alignment: 10
- lighting_shadow_geometry_consistency: 10
- artifact_anatomy_text_reflection_quality: 10
- composition_social_media_usability: 5

## Directory contract
A benchmark run contains sources/, candidates/, refs/, eval/objective/, eval/judges/, eval/human/, reports/ and run.json.

## Pilot rule
Start with P0_CHATGPT_INCLUDED and P1_LOCAL. Escalate only failed representative cases to paid paths. Never bulk-generate from this harness without an external approval gate.

# LunaMatch v8.0.1 — correspondence safety patch

- Fixes OpenCV `remap` SHRT_MAX failures when a geographic tile maps to a native OHRC window wider/taller than 32767 pixels.
- Adds bounded 2-D remapping that partitions the output tile without changing physical GSD.
- Fixes ECC return-value handling: correlation and warp matrix are now read in the correct order.
- Dense ECC model-generated points can no longer independently satisfy the final `VALIDATED` gate; ECC is supporting evidence only.
- Adds regression coverage for oversized native remap and dense-ECC anti-degeneracy.

This release does not claim new real-mission validation. The next run on the user's Chandrayaan-2 products is required to evaluate OHRC↔IIRS after the remap fix and to re-evaluate TMC-2↔IIRS without dense-ECC self-validation.

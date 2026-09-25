# LunaMatch Platform 1.1.0 — interactive demo completion

This is a presentation/UI release around the existing v8.0.2 scientific engine. No scientific validation claim is changed by this patch.

## UX fixes
- Mission scanning is now explicit and visibly reports connection/product count/time.
- Changing the mission-data path requires a fresh scan.
- The diagnostics checkbox visibly changes the UI and controls the diagnostics panel.
- Added first-time-user workflow guidance.
- Removed internal engineering/version language from the visible sidebar.

## Demo completion
- Selected-pair correspondence run remains available.
- Added an optional all-three-pair mission experiment: OHRC↔TMC2, OHRC↔IIRS, TMC2↔IIRS.
- Each run now exports a JSON metrics file and a correspondence-evidence PNG.
- Added an on-screen common-grid correspondence evidence figure using the actual returned points and RANSAC inlier geometry.
- Added batch experiment summary in the Correspondence Lab.
- Added PNG download buttons in Products & Export.

The evidence figure is explicitly labelled as a common-grid correspondence view, not a raw-image overlay, so the UI does not overclaim what the current engine output proves.

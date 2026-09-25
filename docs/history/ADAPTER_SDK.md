# Adapter SDK

Implement a class with:

- `name`
- `can_open(path) -> bool`
- `inspect(path) -> SceneSpec`

`SceneSpec` must expose a canonical array shape/dtype/interleave plus optional GSD, CRS, footprint, acquisition time and solar geometry. The rest of LunaMatch does not depend on the source file format.

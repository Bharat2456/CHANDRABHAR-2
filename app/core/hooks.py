"""Observer interface for progress, evidence capture and cancellation.

The engine only *reports* through these hooks; hooks never change a scientific result.
The default implementation does nothing, so desktop/CLI behaviour is unchanged.
"""
class Hooks:
    def stage(self, name, **info): pass                 # coarse pipeline stage change
    def level_begin(self, index, total, target_gsd_m, grid_h, grid_w, mode): pass
    def tile(self, index, total, **info): pass          # measured tile progress
    def capture(self, oi, oj, ref, src, mask=None): pass  # representation tiles the matcher saw
    def level_end(self, index, result): pass
NULL_HOOKS = Hooks()

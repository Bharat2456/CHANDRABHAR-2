from pathlib import Path
class AdapterRegistry:
    _adapters=[]
    @classmethod
    def register(cls, adapter): cls._adapters.append(adapter); return adapter
    @classmethod
    def inspect(cls, path, root=None):
        """Inspect one product. *root* (optional) confines every companion-file lookup."""
        p=Path(path)
        errors=[]
        for a in cls._adapters:
            try:
                if a.can_open(p): return a.inspect(p, root=root)
            except Exception as e: errors.append(f"{a.name}: {e}")
        raise ValueError("No adapter could inspect product: " + " | ".join(errors))

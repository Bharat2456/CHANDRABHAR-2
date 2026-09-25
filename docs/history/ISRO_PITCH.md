# ISRO-facing technical pitch

LunaMatch is a CPU-first, adapter-driven correspondence pipeline for heterogeneous lunar image products. Its core design separates sensor/file adaptation, physical resolution planning, out-of-core I/O, modality-robust representation, geometric estimation, and evidence gating. This permits migration from local laptops to larger CPU/GPU/HPC infrastructure without changing the scientific contract.

The system is deliberately conservative: weak real-data matches are not promoted to success. Mission-specific product IDs and metadata remain traceable, while new PDS4/GeoTIFF/ENVI/raw formats can be added through the adapter boundary.

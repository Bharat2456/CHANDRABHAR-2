from app.adapters.base import AdapterRegistry
from app.adapters.pds4 import PDS4Adapter
from app.adapters.envi import ENVIAdapter
from app.adapters.numpy_adapter import NumpyAdapter
from app.adapters.raw_sidecar import RawSidecarAdapter
for _a in (PDS4Adapter,ENVIAdapter,NumpyAdapter,RawSidecarAdapter): AdapterRegistry.register(_a)

"""Bounded CPU Float32 cognitive state prototype, not a compiled Mojo backend.

No imaginary photonic/FPGA throughput or implicit device execution.
"""
from array import array
from dataclasses import dataclass
from math import isfinite
from typing import Iterable


class TensorError(ValueError):
    pass


def _finite(value):
    if type(value) not in (int, float):
        raise TensorError("Finite numeric element expected")
    try:
        converted = float(value)
    except (OverflowError, ValueError) as exc:
        raise TensorError("Out-of-range numeric element") from exc
    if not isfinite(converted) or abs(converted)>3.4e38:
        raise TensorError("Float32 value must be finite and representable")
    return converted


class TensorBank:
    """Typed Float32 contiguous 1-D array; max 1,000,000 elements.

    update() validates everything before commit; failure leaves original state.
    """

    MAX_DIMENSION = 1_000_000

    def __init__(self, dimensions):
        if type(dimensions) is not int or not 1<=dimensions<=self.MAX_DIMENSION:
            raise TensorError("dimensions must be 1..1_000_000")
        self.dimensions = dimensions
        self._state = array("f", [0.0])*dimensions

    def update(self, delta):
        if not isinstance(delta, (array, list, tuple)) or len(delta)!=self.dimensions:
            raise TensorError("Delta shape must equal state dimension")
        # A staged write avoids partially updated tensors on validation failure.
        staged=array("f")
        for current, inc in zip(self._state,delta):
            value=float(current)+_finite(inc)
            if not isfinite(value) or abs(value)>3.4e38:
                raise TensorError("Float32 sum overflow")
            staged.append(value)
        self._state=staged
        return {"elements_updated":self.dimensions,"dtype":"float32","backend":"cpu_reference"}

    def at(self,index):
        if type(index) is not int or not 0<=index<self.dimensions:
            raise TensorError("Tensor index out of bounds")
        return float(self._state[index])

    def snapshot(self,max_elements=4096):
        if type(max_elements) is not int or not 1<=max_elements<=self.MAX_DIMENSION:
            raise TensorError("Invalid snapshot limit")
        if self.dimensions>max_elements:
            raise TensorError("Explicitly increase snapshot limit for large state")
        return list(self._state)


@dataclass(frozen=True)
class HardwareCapability:
    name: str
    enabled: bool
    verified: bool
    interface: str


CAPABILITIES = {
    1: HardwareCapability("passage_l20_photonic",False,False,"UNVERIFIED"),
    2: HardwareCapability("ice40_fpga_evolvable",False,False,"UNVERIFIED"),
}


def hardware_dispatch_plan(task_id,tensor_dimensions):
    """Honest capability report only: never touches hardware."""
    if type(task_id) is not int or type(tensor_dimensions) is not int:
        raise TensorError("IDs and dimensions must be integers")
    if not 1<=tensor_dimensions<=TensorBank.MAX_DIMENSION:
        raise TensorError("Invalid tensor dimension")
    cap=CAPABILITIES.get(task_id)
    if cap is None:
        return {"status":"DENIED","reason":"unknown_task","side_effects":False}
    return {"status":"UNAVAILABLE",
            "capability":cap.name,"hardware_verified":False,
            "reason":"no_driver_no_attestation_no_performance_measurement",
            "side_effects":False}

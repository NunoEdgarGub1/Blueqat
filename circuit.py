import numpy as np
import gate

DEFAULT_GATE_SET = {
    "i": gate.IGate,
    "z": gate.ZGate,
    "x": gate.XGate,
    "h": gate.HGate,
    "cz": gate.CZGate,
    "cx": gate.CXGate,
    "cnot": gate.CXGate,
    "rz": gate.RZGate,
    "phase": gate.RZGate,
    "u1": gate.RZGate,
    "measure": gate.Measurement,
    "m": gate.Measurement,
    "dbg": gate.DebugDisplay,
}
DEFAULT_DTYPE = np.complex128

class Circuit:
    def __init__(self, gate_set=None, ops=None, n_qubits=0):
        self.gate_set = gate_set or DEFAULT_GATE_SET.copy()
        self.ops = ops or []
        self.n_qubits = n_qubits
        self.run_history = []

    def __getattr__(self, name):
        if name in self.gate_set:
            return _GateWrapper(self, self.gate_set[name])
        raise AttributeError("'circuit' object has no attribute or gate '" + name + "'")

    def copy(self):
        return Circuit(self.gate_set, self.ops, self.n_qubits)

    def run(self):
        n_qubits = self.n_qubits
        qubits = np.zeros(2**n_qubits, dtype=DEFAULT_DTYPE)
        qubits[0] = 1.0
        helper = {
            "n_qubits": n_qubits,
            "indices": np.arange(2**n_qubits, dtype=np.uint32),
            "cregs": [0] * n_qubits,
        }
        for op in self.ops:
            gate = op.gate(*op.args, **op.kwargs)
            qubits = gate.apply(helper, qubits, op.target)
        self.run_history.append(tuple(helper["cregs"]))
        return qubits

    def last_result(self):
        try:
            return self.run_history[-1]
        except IndexError:
            raise ValueError("The Circuit has never been to run.")

class _GateWrapper:
    def __init__(self, circuit, gate):
        self.circuit = circuit
        self.target = None
        self.gate = gate
        self.args = ()
        self.kwargs = {}

    def __call__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        return self

    def __getitem__(self, args):
        self.target = args
        self.circuit.n_qubits = max(gate.get_maximum_index(args) + 1, self.circuit.n_qubits)
        self.circuit.ops.append(self)
        return self.circuit

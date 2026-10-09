import unittest
from omega_builder.edge import tensor_core, hdc, thermodynamics

class Tests(unittest.TestCase):
    def test_tensor(self):
        t=tensor_core.TensorBank(2)
        t.update([1.0,2.0])
        self.assertEqual(t.snapshot(),[1.0,2.0])
    def test_hdc(self):
        result=hdc.reference_associative_retrieval(64)
        self.assertTrue(result['exact_single_pair_recovery'])
    def test_ising(self):
        a=thermodynamics.cpu_gibbs_reference(samples=3,seed=42)
        self.assertEqual(len(a['spins']),3)

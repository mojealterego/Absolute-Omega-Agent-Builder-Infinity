import unittest
from omega_builder.edge import mesh,mutation_gate as gate

SECRET=b'example-key-for-tests-at-least-32-bytes'
REVIEW=b'reviewer-key-for-tests-at-least-32-bytes'

class MeshSecurity(unittest.TestCase):
    def example(self):
        return mesh.sign_event('omega/edge/state/node_A','state',{'value':3},SECRET,
                               nonce='0'*32,timestamp=1000)
    def test_verify_and_roundtrip(self):
        a=self.example()
        self.assertEqual(mesh.decode_event(mesh.encode_event(a)),a)
        self.assertEqual(mesh.verify_event(a,SECRET,now=1000)['payload'],{'value':3})
    def test_tamper(self):
        a=self.example();a['payload']['value']=9
        with self.assertRaises(mesh.MeshError):mesh.verify_event(a,SECRET,now=1000)
    def test_nonce_replay(self):
        a=self.example();g=mesh.ReplayGuard()
        mesh.verify_event(a,SECRET,now=1000,replays=g)
        with self.assertRaises(mesh.MeshError):
            mesh.verify_event(a,SECRET,now=1000,replays=g)
    def test_expiry(self):
        with self.assertRaises(mesh.MeshError):
            mesh.verify_event(self.example(),SECRET,now=2000)
    def test_network_default_disabled(self):
        with self.assertRaises(mesh.MeshError):
            mesh.zenoh_publish(self.example(),SECRET)
    def test_invalid_topic(self):
        with self.assertRaises(mesh.MeshError):
            mesh.sign_event('omega/edge/other/node_A','other',{},SECRET)

class MutationEvidence(unittest.TestCase):
    def sample(self):
        return {'candidate_id':'x','candidate_kind':'source_patch',
                'artifact_sha256':gate.sha256_bytes(b'a'),
                'baseline_sha256':gate.sha256_bytes(b'b'),
                'alignment_score':85,'human_safety_flag':True,
                'tests_passed':True,'security_scan_passed':True}
    def test_signed_review_is_not_execution(self):
        candidate=self.sample()
        s=gate.sign_review(candidate,REVIEW)
        result=gate.assess_candidate(candidate,s,REVIEW)
        self.assertEqual(result['status'],'ELIGIBLE_FOR_SEPARATE_HUMAN_DEPLOYMENT')
        self.assertFalse(result['executed'])
    def test_signed_tampering_fails(self):
        candidate=self.sample();signature=gate.sign_review(candidate,REVIEW)
        candidate['artifact_sha256']=gate.sha256_bytes(b'other')
        self.assertEqual(gate.assess_candidate(candidate,signature,REVIEW)['status'],'DENIED')
    def test_declared_policy_conditions(self):
        for field,value in [('alignment_score',79),('human_safety_flag',False),
                            ('tests_passed',False),('security_scan_passed',False)]:
            item=self.sample();item[field]=value
            result=gate.assess_candidate(item,gate.sign_review(item,REVIEW),REVIEW)
            self.assertEqual(result['status'],'DENIED')
    def test_invalid_manifest(self):
        item=self.sample();item['candidate_kind']='arbitrary'
        with self.assertRaises(gate.GateError):gate.sign_review(item,REVIEW)

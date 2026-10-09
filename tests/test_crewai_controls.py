"""Offline CrewAI flow guard and memory regression tests (no agent started)."""
import unittest
from omega_builder import crew_flow_guard as f,crew_memory as m


def policy(**kw):
    return f.FlowPolicy([
        f.Step("collect","review",None,2,("search_docs",)),
        f.Step("review",None,None,1,("write_report",))],
        "collect",**kw)


class FlowTests(unittest.TestCase):
    def test_replay_matches(self):
        run=f.OfflineFlow(policy())
        run.record("collect",False,4,"failX")
        run.record("collect",True,7,"successX")
        replayed=f.replay_flow(run.policy,run.audit)
        self.assertEqual(replayed,run.snapshot())

    def test_replay_rejects_modified_audit(self):
        run=f.OfflineFlow(policy())
        run.record("collect",True,1,"receiptX")
        events=[dict(event) for event in run.audit]
        events[0]["cost_micro_usd"]=99
        with self.assertRaises(f.FlowPolicyError):
            f.replay_flow(run.policy,events,expected_sha256=run.snapshot()["audit_sha256"])

    def test_long_hash_chain_budget(self):
        steps=[f.Step("s",None,None,10)]
        flow=f.OfflineFlow(f.FlowPolicy(steps,"s",max_events=1000))
        for i in range(9):
            flow.record("s",False,0,"receipt"+str(i))
        self.assertEqual(len(flow.snapshot()["audit_sha256"]),64)

    def test_successful_bounded_flow(self):
        run=f.OfflineFlow(policy())
        a=run.record("collect",True,10,"receipt1")
        self.assertEqual(a["current"],"review")
        b=run.record("review",True,20,"receipt2")
        self.assertEqual(b["status"],"COMPLETE")
        self.assertEqual(b["spent_micro_usd"],30)
        self.assertFalse(b["executed_by_library"])

    def test_retry_then_failure(self):
        run=f.OfflineFlow(policy())
        a=run.record("collect",False,1,"failure1")
        self.assertEqual(a["current"],"collect")
        b=run.record("collect",False,1,"failure2")
        self.assertEqual(b["status"],"FAILED")

    def test_duplicate_receipt(self):
        run=f.OfflineFlow(policy())
        run.record("collect",False,1,"same")
        with self.assertRaises(f.FlowPolicyError):
            run.record("collect",True,1,"same")

    def test_wrong_step_rejected(self):
        run=f.OfflineFlow(policy())
        with self.assertRaises(f.FlowPolicyError):
            run.record("review",True,0,"bad")

    def test_cost_limit_blocks(self):
        run=f.OfflineFlow(policy(max_cost_micro_usd=5))
        result=run.record("collect",True,6,"expense")
        self.assertEqual(result["status"],"BLOCKED_BUDGET")
        self.assertEqual(result["spent_micro_usd"],0)

    def test_events_limit_blocks(self):
        run=f.OfflineFlow(policy(max_events=1))
        run.record("collect",True,0,"r1")
        self.assertEqual(run.record("review",True,0,"r2")["status"],"BLOCKED_BUDGET")

    def test_reject_cycle(self):
        with self.assertRaises(f.FlowPolicyError):
            f.FlowPolicy([f.Step("a","b",None),f.Step("b","a",None)],"a")

    def test_reject_dangling(self):
        with self.assertRaises(f.FlowPolicyError):
            f.FlowPolicy([f.Step("a","missing",None)],"a")

    def test_reject_unreachable(self):
        with self.assertRaises(f.FlowPolicyError):
            f.FlowPolicy([f.Step("a",None,None),f.Step("b",None,None)],"a")

    def test_tool_allowlist(self):
        p=policy()
        self.assertTrue(f.tool_intent(p,"collect","search_docs",{"q":"test"})["eligible_for_separate_executor"])
        self.assertFalse(f.tool_intent(p,"collect","write_report",{})["eligible_for_separate_executor"])

    def test_tool_mutation_needs_exact_review(self):
        p=policy()
        args={"filename":"public_report.txt"}
        self.assertFalse(f.tool_intent(p,"review","write_report",args,readonly=False)["eligible_for_separate_executor"])
        digest=f.argument_sha256(args)
        review=f.tool_intent(p,"review","write_report",args,readonly=False,approved_sha256=digest)
        self.assertTrue(review["eligible_for_separate_executor"])
        self.assertFalse(review["identity_verified"])
        self.assertFalse(review["executed"])
        self.assertFalse(f.tool_intent(p,"review","write_report",{"filename":"secret"},readonly=False,approved_sha256=digest)["eligible_for_separate_executor"])

    def test_bad_types(self):
        with self.assertRaises(f.FlowPolicyError):
            f.Step("x",None,None,max_attempts=True)
        with self.assertRaises(f.FlowPolicyError):
            f.argument_sha256({"x":float("nan")})

class MemoryTests(unittest.TestCase):
    def item(self,ident,scope,source,when,importance,vector):
        return {"id":ident,"scope":scope,"source":source,"recorded_ms":when,
                "importance":importance,"vector":vector}

    def test_identical_beats_orthogonal(self):
        data=[self.item("same","user1","local",100,0,[1,0]),
              self.item("other","user1","local",100,0,[0,1])]
        out=m.rank_memories([1,0],data,scope="user1",now_ms=100)
        self.assertEqual(out["results"][0]["id"],"same")
        self.assertFalse(out["external_text_emitted"])

    def test_scope_isolation_and_future(self):
        data=[self.item("foreign","tenant2","local",9,1,[1,0]),
              self.item("future","tenant1","local",101,1,[1,0]),
              self.item("valid","tenant1","local",100,0,[1,0])]
        out=m.rank_memories([1,0],data,scope="tenant1",now_ms=100)
        self.assertEqual([x["id"] for x in out["results"]],["valid"])

    def test_recency_half_life(self):
        data=[self.item("new","t","s",100,0,[1,0]),
              self.item("old","t","s",90,0,[1,0])]
        out=m.rank_memories([1,0],data,scope="t",now_ms=100,half_life_ms=10)
        self.assertGreater(out["results"][0]["recency"],out["results"][1]["recency"])
        self.assertAlmostEqual(out["results"][1]["recency"],.5)

    def test_importance(self):
        data=[self.item("a","t","s",0,0,[1,0]),
              self.item("b","t","s",0,1,[1,0])]
        out=m.rank_memories([1,0],data,scope="t",now_ms=0)
        self.assertEqual(out["results"][0]["id"],"b")

    def test_zero_vector_and_malformed_record_rejected(self):
        with self.assertRaises(m.MemoryScoreError):
            m.rank_memories([0,0],[],scope="t",now_ms=1)
        with self.assertRaises(m.MemoryScoreError):
            m.rank_memories([1], [{"id":"x"}],scope="t",now_ms=1)

    def test_scoring_weights_checked(self):
        with self.assertRaises(m.MemoryScoreError):
            m.rank_memories([1],[self.item("a","t","s",0,1,[1])],scope="t",now_ms=0,weights=(1,1,1))

    def test_duplicate_id_rejected(self):
        row=self.item("a","t","s",0,1,[1])
        with self.assertRaises(m.MemoryScoreError):
            m.rank_memories([1],[row,row],scope="t",now_ms=0)


if __name__=="__main__":
    unittest.main()

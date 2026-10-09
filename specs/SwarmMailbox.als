// Snapshot model: not a distributed implementation proof.
abstract sig Stage {}
one sig Queued, Leased, Done extends Stage {}
sig Worker {}
sig Task { stage: one Stage, owner: lone Worker }
fact StateAndLease {
  all t: Task | (t.stage = Leased) iff (one t.owner)
  all t: Task | (t.stage != Leased) implies (no t.owner)
}
assert ExclusiveWorker {
  all disj t1, t2: Task | no (t1.owner & t2.owner)
}
check ExclusiveWorker for 3 Task, 2 Worker

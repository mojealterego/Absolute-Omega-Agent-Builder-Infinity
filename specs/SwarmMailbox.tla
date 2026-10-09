----------------------------- MODULE SwarmMailbox -----------------------------
EXTENDS Naturals, FiniteSets, TLC
CONSTANTS Tasks, Workers
VARIABLES state, owner
vars == <<state, owner>>

Init == /\ state = [t \in Tasks |-> "queued"]
        /\ owner = [t \in Tasks |-> "none"]

Claim(t, w) ==
    /\ state[t] = "queued"
    /\ \A o \in Tasks : owner[o] # w
    /\ state' = [state EXCEPT ![t] = "leased"]
    /\ owner' = [owner EXCEPT ![t] = w]

Complete(t, w) ==
    /\ state[t] = "leased" /\ owner[t] = w
    /\ state' = [state EXCEPT ![t] = "done"]
    /\ owner' = [owner EXCEPT ![t] = "none"]

Release(t, w) ==
    /\ state[t] = "leased" /\ owner[t] = w
    /\ state' = [state EXCEPT ![t] = "queued"]
    /\ owner' = [owner EXCEPT ![t] = "none"]

Next == \E t \in Tasks, w \in Workers :
            Claim(t,w) \/ Complete(t,w) \/ Release(t,w)

TypeOK ==
    /\ state \in [Tasks -> {"queued","leased","done"}]
    /\ owner \in [Tasks -> (Workers \cup {"none"})]

LeaseAligned == \A t \in Tasks : (state[t] = "leased") <=> (owner[t] # "none")
OneLeasePerWorker == \A w \in Workers :
    Cardinality({t \in Tasks : owner[t] = w}) <= 1
NoNonterminalDeadlock ==
    (\E t \in Tasks : state[t] # "done") => ENABLED Next

Spec == Init /\ [][Next]_vars
=============================================================================

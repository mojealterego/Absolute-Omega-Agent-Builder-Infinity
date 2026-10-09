/-
Lean 4 reference property: structurally excludes low-score or unsafe-flag
states from satisfying a *declared* gate predicate. No model alignment claim.
This file must be compiled with a pinned Lean 4 toolchain before saying it is
machine-checked. No runtime mutation is authorized by this source.
-/
import Mathlib.Data.Nat.Basic

structure MutationState where
  alignmentScore : Nat
  humanSafetyFlag : Bool
  testsPassed : Bool
  securityScanPassed : Bool

def qualifies (s : MutationState) : Prop :=
  s.humanSafetyFlag = true ∧
  s.alignmentScore ≥ 80 ∧
  s.testsPassed = true ∧
  s.securityScanPassed = true

theorem unsafeFlagCannotQualify (s : MutationState)
    (h : s.humanSafetyFlag = false) : ¬ qualifies s := by
  intro hs
  have ht : s.humanSafetyFlag = true := hs.1
  simp [h] at ht

theorem lowScoreCannotQualify (s : MutationState)
    (h : s.alignmentScore < 80) : ¬ qualifies s := by
  intro hs
  exact (Nat.not_le_of_gt h) hs.2.1

theorem failedTestsCannotQualify (s : MutationState)
    (h : s.testsPassed = false) : ¬ qualifies s := by
  intro hs
  have ht : s.testsPassed = true := hs.2.2.1
  simp [h] at ht

theorem failedScanCannotQualify (s : MutationState)
    (h : s.securityScanPassed = false) : ¬ qualifies s := by
  intro hs
  have ht : s.securityScanPassed = true := hs.2.2.2
  simp [h] at ht

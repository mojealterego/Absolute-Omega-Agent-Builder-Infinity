"""ML validation, visualization and governance regression tests. No Zeus."""
import importlib.util
import math
import unittest
from omega_builder import ml_validation as v, ml_embeddings as e, ml_visualization as vis, ml_governance as g
from omega_builder.mathematics.api import calculate,MathAPIError


class Evaluation(unittest.TestCase):
    def test_split_disjoint(self):
        result=v.split_indices(50,.2,.2,seed=42)
        a,b,c=(set(result[x]) for x in ("train","validation","test"))
        self.assertFalse(a&b or b&c or a&c)
        self.assertEqual(a|b|c,set(range(50)))
        self.assertEqual(result,v.split_indices(50,.2,.2,seed=42))

    def test_stratified_split(self):
        labels=["N"]*15+["P"]*15
        out=v.split_indices(len(labels),.2,.2,seed=12,labels=labels)
        for name in ("train","validation","test"):
            values={labels[j] for j in out[name]}
            self.assertEqual(values,{"N","P"})

    def test_too_rare_class_fails_closed(self):
        with self.assertRaises(v.ValidationError):
            v.split_indices(6,.2,.2,labels=["X"]*5+["Y"])

    def test_stratified_kfold(self):
        labels=["A"]*10+["B"]*10
        partitions=v.kfold_indices(20,5,seed=10,labels=labels)
        self.assertEqual(len(partitions),5)
        test_union=[i for fold in partitions for i in fold["test"]]
        self.assertEqual(sorted(test_union),list(range(20)))
        self.assertTrue(all(set(fold["train"]).isdisjoint(fold["test"]) for fold in partitions))
        self.assertTrue(all({labels[j] for j in fold["test"]}=={"A","B"} for fold in partitions))

    def test_loocv(self):
        parts=v.leave_one_out(4)
        self.assertEqual(len(parts),4)
        self.assertTrue(all(len(part["test"])==1 and len(part["train"])==3 for part in parts))

    def test_multiclass_metrics(self):
        report=v.classification_report(["a","a","b","b"],["a","b","b","b"])
        self.assertAlmostEqual(report["accuracy"],.75)
        self.assertAlmostEqual(report["balanced_accuracy"],.75)
        self.assertAlmostEqual(report["macro_f1"],(2/3+.8)/2)
        self.assertEqual(report["confusion_matrix"],[[1,1],[0,2]])

    def test_monte_carlo_separate_from_cv(self):
        self.assertNotEqual(v.kfold_indices(8,4),v.kfold_indices(8,4,seed=10))

    def test_drift_ks(self):
        self.assertAlmostEqual(v.ks_distance([1,2,3],[1,2,3]),0.)
        self.assertAlmostEqual(v.ks_distance([1,1,1],[9,9,9]),1.)

    def test_psi(self):
        x=list(range(100))
        self.assertAlmostEqual(v.psi(x,x)["psi"],0.)
        self.assertGreater(v.psi(x,[v+200 for v in x])["psi"],0.)
        self.assertEqual(v.psi(x,x)["scope"],"heuristic_covariate_drift_only")

    def test_smote_binary(self):
        data=[[0.],[1.],[2.],[3.],[10.],[11.]]
        labels=[0,0,0,0,1,1]
        out=v.smote_train(data,labels,neighbors=1,seed=17)
        self.assertEqual(len(out["X"]),8)
        self.assertEqual(out["synthetic"],2)
        self.assertEqual(out["y"].count(0),out["y"].count(1))
        self.assertEqual(out,v.smote_train(data,labels,neighbors=1,seed=17))

    def test_smote_minority_guard(self):
        with self.assertRaises(v.ValidationError):
            v.smote_train([[1],[2],[3],[4]],[0,0,0,1],neighbors=1)

    def test_uncertainty(self):
        ranked=v.active_learning_uncertainty([[.99,.01],[.5,.5]],top_k=1)
        self.assertEqual(ranked[0]["index"],1)


class Visual(unittest.TestCase):
    def test_histogram_counts(self):
        h=vis.histogram([0,0,1,2],bins=2)
        self.assertEqual(sum(h["counts"]),4)
        self.assertEqual(vis.histogram([1,1])["counts"],[2])

    def test_box_summary(self):
        box=vis.boxplot_summary([1,2,3,4,5])
        self.assertAlmostEqual(box["median"],3.)

    def test_scatter(self):
        self.assertEqual(vis.scatter_points([0,1],[2,3])["n"],2)
        with self.assertRaises(v.ValidationError):
            vis.scatter_points([1,2],[1])

    def test_heatmap(self):
        self.assertEqual(vis.heatmap_matrix([[1,2],[3,4]])["max"],4.)
        with self.assertRaises(v.ValidationError):
            vis.heatmap_matrix([[1,2],[3]])

    def test_no_arbitrary_plot_type(self):
        with self.assertRaises(v.ValidationError):
            vis.render_png("code_injection",[1,2],"anything.png")


class Embeddings(unittest.TestCase):
    def test_lda_real_or_missing(self):
        x=[[1,1],[1.2,1],[.8,.9],[5,5],[5.2,5],[4.8,4.9]]
        y=["a"]*3+["b"]*3
        if importlib.util.find_spec("sklearn") is None:
            with self.assertRaises(e.EmbeddingError):
                e.lda_fit(x,y)
        else:
            model=e.lda_fit(x,y)
            out=e.lda_transform([[1,1],[5,5]],model)
            self.assertEqual(len(out),2)
            self.assertEqual(len(out[0]),1)
            self.assertEqual(model["fit_scope"],"training_only")

    def test_lda_unbalanced_rejected(self):
        with self.assertRaises(e.EmbeddingError):
            e.lda_fit([[1],[2],[3],[4]],["a","a","a","b"])

    def test_tsne_requires_perplexity_less_than_n(self):
        with self.assertRaises(e.EmbeddingError):
            e.tsne_embedding([[1],[2],[3],[4]],perplexity=5)

    def test_tsne_backend_or_missing(self):
        x=[[j, j % 3] for j in range(12)]
        if importlib.util.find_spec("sklearn") is None:
            with self.assertRaises(e.EmbeddingError):
                e.tsne_embedding(x,perplexity=3)
        else:
            result=e.tsne_embedding(x,perplexity=3,seed=1)
            self.assertEqual(len(result["embedding"]),12)
            self.assertEqual(len(result["embedding"][0]),2)

    def test_umap_invalid_neighbours(self):
        with self.assertRaises(e.EmbeddingError):
            e.umap_embedding([[1],[2],[3],[4]],neighbors=4)

    def test_autoencoder_real_or_missing(self):
        x=[[0,0],[1,1],[.5,.5],[.2,.2]]
        if importlib.util.find_spec("numpy") is None:
            with self.assertRaises(e.EmbeddingError):
                e.autoencoder_fit(x,latent_dim=1,epochs=10)
        else:
            trained=e.autoencoder_fit(x,latent_dim=1,epochs=80,seed=3)
            self.assertTrue(math.isfinite(trained["train_mse"]))
            self.assertEqual(len(e.autoencoder_transform(x,trained)[0]),1)
            self.assertEqual(len(e.autoencoder_reconstruct(x,trained)[0]),2)

    def test_autoencoder_bad_latent(self):
        with self.assertRaises(e.EmbeddingError):
            e.autoencoder_fit([[1],[2],[3],[4]],latent_dim=1)


class Governance(unittest.TestCase):
    def test_data_quality(self):
        report=g.dataset_quality([{"x":1},{"x":1},{"y":2}])
        self.assertEqual(report["duplicate_rows"],1)
        self.assertEqual(report["missing_counts"]["x"],1)

    def test_detect_split_overlap(self):
        out=g.split_overlap([{"x":1}],[{"x":2}],[{"x":1}])
        self.assertTrue(out["potential_leakage"])
        self.assertEqual(out["overlap_by_content"]["train_test"],1)

    def test_deterministic_fingerprint(self):
        self.assertEqual(g.fingerprint({"b":1,"a":2}),g.fingerprint({"a":2,"b":1}))

    def test_weak_supervision(self):
        out=g.weak_supervision([{"text":"cat"},{"text":"dog"},{"text":"dog cat"},{"text":"other"}],
                               "text",{"feline":["cat"],"canine":["dog"]})
        self.assertEqual(out["labels"],["feline","canine",None,None])
        self.assertEqual(out["abstentions"],2)

    def test_hmac_pseudonyms(self):
        key=b"one super secret key held offsite"
        self.assertEqual(g.pseudonymize("alice",key),g.pseudonymize("alice",key))
        self.assertNotEqual(g.pseudonymize("alice",key),g.pseudonymize("bob",key))
        with self.assertRaises(g.GovernanceError):
            g.pseudonymize("alice",b"short")

    def test_redaction_scope(self):
        out=g.redact_common_identifiers("Email john@example.com ID 12345678901")
        self.assertNotIn("john@example.com",out)
        self.assertNotIn("12345678901",out)

    def test_fairness_group_size(self):
        groups=["g1"]*5+["g2"]*5
        a=[1,1,1,0,0,1,1,0,0,0]
        b=[1,1,1,0,0,0,0,0,0,0]
        report=g.binary_group_metrics(a,b,groups)
        self.assertGreater(report["selection_rate_gap"],0)
        with self.assertRaises(g.GovernanceError):
            g.binary_group_metrics(a,b,groups,min_size=10)

    def test_conflicting_labels(self):
        rep=g.classification_conflicts([[1],[1],[2]],[1,0,1])
        self.assertEqual(rep["conflicting_rows"],1)

    def test_concept_drift_observed(self):
        out=g.concept_drift_report([0,0,1],[0,0,1],[0,0,1],[1,0,0])
        self.assertLess(out["accuracy_delta"],0)


class API(unittest.TestCase):
    def test_validation_dispatch(self):
        out=calculate({"operation":"validation.ks_distance",
                       "args":{"reference":[1,2],"current":[10,11]}})
        self.assertAlmostEqual(out["result"],1.)

    def test_visualization_dispatch(self):
        out=calculate({"operation":"visualization.histogram",
                       "args":{"values":[1,2,3],"bins":2}})
        self.assertEqual(sum(out["result"]["counts"]),3)

    def test_weak_supervision_dispatch(self):
        out=calculate({"operation":"governance.dataset_quality",
                       "args":{"rows":[{"x":1}]}})
        self.assertEqual(out["result"]["rows"],1)

    def test_reject_hmac_secrets_via_math_json(self):
        with self.assertRaises(MathAPIError):
            calculate({"operation":"governance.pseudonymize","args":{}})


if __name__=="__main__":
    unittest.main()

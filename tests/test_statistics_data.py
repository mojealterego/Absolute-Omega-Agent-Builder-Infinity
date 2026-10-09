"""Mathematical extension: empirical tests and regression checks."""
import math
import sqlite3
import unittest

from omega_builder.mathematics import statistics as s, information as i
from omega_builder import preprocessing as p
from omega_builder.storage import SQLiteKnowledgeStore, StoreError
from omega_builder.mathematics.api import calculate, MathAPIError
from omega_builder.mathematics.probability import ProbabilityError


class DistributionTests(unittest.TestCase):
    def test_pearson_and_covariance(self):
        self.assertAlmostEqual(s.pearson([1,2,3],[2,4,6]),1.)
        self.assertAlmostEqual(s.pearson([1,2,3],[6,4,2]),-1.)
        self.assertAlmostEqual(s.covariance([1,2,3],[2,4,6]),2.)

    def test_correlation_constant_rejected(self):
        with self.assertRaises(ProbabilityError):
            s.pearson([1,1,1],[2,3,4])

    def test_mle_moments(self):
        self.assertAlmostEqual(s.sample_mean([1,3]),2.)
        self.assertAlmostEqual(s.sample_variance([1,3]),2.)
        self.assertEqual(s.mle_gaussian([1,3]),{"mean":2.,"variance_mle":1.})
        self.assertAlmostEqual(s.mle_bernoulli([1,0,1]),2/3)

    def test_map_vs_posterior(self):
        obs=[1,0,1,1]
        self.assertAlmostEqual(s.map_bernoulli_beta(obs,2,2),4/6)
        self.assertAlmostEqual(s.posterior_mean_bernoulli_beta(obs,2,2),5/8)
        with self.assertRaises(ProbabilityError):
            s.map_bernoulli_beta([],1,1)

    def test_bernoulli_binomial(self):
        self.assertAlmostEqual(s.bernoulli_pmf(1,.25),.25)
        self.assertAlmostEqual(s.bernoulli_pmf(0,.25),.75)
        self.assertAlmostEqual(s.binomial_pmf(2,3,.5),.375)
        self.assertAlmostEqual(sum(s.binomial_pmf(k,6,.3) for k in range(7)),1.)

    def test_poisson(self):
        self.assertAlmostEqual(s.poisson_pmf(0,2),math.exp(-2))
        self.assertAlmostEqual(sum(s.poisson_pmf(k,3.) for k in range(30)),1.,places=9)

    def test_normal_and_exponential(self):
        self.assertAlmostEqual(s.normal_cdf(0.),.5)
        self.assertAlmostEqual(s.exponential_pdf(0,2),2.)
        self.assertAlmostEqual(s.exponential_cdf(1,2),1-math.exp(-2))

    def test_uniform_beta_gamma(self):
        self.assertAlmostEqual(s.uniform_pdf(.5,0,1),1.)
        self.assertAlmostEqual(s.uniform_pdf(2,0,1),0.)
        self.assertAlmostEqual(s.beta_pdf(.5,1,1),1.)
        self.assertAlmostEqual(s.gamma_pdf(2,1,2),math.exp(-1)/2)
        with self.assertRaises(ProbabilityError):
            s.beta_pdf(0,2,3)

    def test_rate_parameter_validation(self):
        with self.assertRaises(ProbabilityError):
            s.poisson_pmf(2,-1)
        with self.assertRaises(ProbabilityError):
            s.exponential_pdf(.3,0)
        with self.assertRaises(ProbabilityError):
            s.binomial_pmf(2,2,1.5)

    def test_markov_step(self):
        result=s.markov_step([1.,0.],[[.6,.4],[.3,.7]])
        self.assertEqual(result,[.6,.4])
        result2=s.markov_step(result,[[.6,.4],[.3,.7]])
        self.assertAlmostEqual(result2[0],.48)
        with self.assertRaises(ProbabilityError):
            s.markov_step([1.,0.],[[.6,.6],[.3,.7]])

    def test_random_walk_determinism(self):
        self.assertEqual(s.random_walk(100,seed=5),s.random_walk(100,seed=5))
        self.assertEqual(len(s.random_walk(3,seed=5)),4)

    def test_monte_carlo_estimation(self):
        est=s.monte_carlo_pi(15000,seed=12)
        self.assertEqual(est,s.monte_carlo_pi(15000,seed=12))
        self.assertLess(abs(est["estimate"]-math.pi),.08)


class InformationTests(unittest.TestCase):
    def test_perfect_correlation(self):
        joint=[[.5,0],[0,.5]]
        self.assertAlmostEqual(i.mutual_information(joint),1.)
        self.assertAlmostEqual(i.conditional_entropy_y_given_x(joint),0.)
        self.assertAlmostEqual(i.joint_entropy(joint),1.)

    def test_independence(self):
        joint=[[.25,.25],[.25,.25]]
        self.assertAlmostEqual(i.mutual_information(joint),0.)
        self.assertAlmostEqual(i.conditional_entropy_y_given_x(joint),1.)
        self.assertAlmostEqual(i.joint_entropy(joint),2.)

    def test_invalid_joint(self):
        with self.assertRaises(ProbabilityError):
            i.mutual_information([[.5,.6]])

    def test_snr_capacity(self):
        self.assertAlmostEqual(i.signal_to_noise_db(100,1),20.)
        self.assertAlmostEqual(i.shannon_hartley(1000,3),2000.)

    def test_huffman_roundtrip(self):
        codes=i.huffman_codes({"A":5,"B":2,"C":1,"D":1})
        self.assertEqual(len(set(codes.values())),4)
        sample=["A","B","C","A","D"]
        data=i.huffman_encode(sample,codes)
        self.assertEqual(i.huffman_decode(data,codes),sample)

    def test_huffman_one_symbol(self):
        code=i.huffman_codes({"X":7})
        self.assertEqual(code,{"X":"0"})
        self.assertEqual(i.huffman_decode("000",code),["X"]*3)

    def test_bad_codebook_fails(self):
        with self.assertRaises(ProbabilityError):
            i.huffman_decode("001",{"X":"0","Y":"01"})
        with self.assertRaises(ProbabilityError):
            i.huffman_decode("1",{"X":"0"})


class PreprocessingTests(unittest.TestCase):
    def test_dedup_json_rows(self):
        rows=[{"x":1,"y":2},{"y":2,"x":1},{"x":3}]
        self.assertEqual(p.deduplicate_rows(rows),[rows[0],rows[2]])

    def test_fit_transform_train_only(self):
        train=[{"x":1},{"x":3},{"x":None}]
        spec=p.fit_numeric(train,"x")
        self.assertEqual(spec["impute"],2.)
        val=p.transform_numeric([{"x":100},{"x":None}],spec)
        self.assertEqual(val[1],(spec["impute"]-spec["mean"])/spec["scale"])
        self.assertGreater(val[0],10.)
        self.assertEqual(spec["fit_scope"],"training_only")

    def test_constant_feature(self):
        spec=p.fit_numeric([{"x":2},{"x":2}],"x")
        self.assertTrue(spec["constant"])
        self.assertEqual(p.transform_numeric([{"x":2}],spec),[0.])

    def test_unknown_category_fail_closed(self):
        fit=p.one_hot_fit([{"color":"blue"},{"color":"red"}],"color")
        self.assertEqual(p.one_hot_transform([{"color":"red"}],fit)["vectors"],[[0,1]])
        with self.assertRaises(p.PreprocessingError):
            p.one_hot_transform([{"color":"green"}],fit)

    def test_iqr_flags(self):
        values=[1,1,2,2,3,3,4,100]
        bounds=p.iqr_bounds(values)
        flags=p.outlier_flags(values,bounds)
        self.assertEqual(flags[-1],True)
        self.assertEqual(flags[0],False)

    def test_bad_numeric_input(self):
        with self.assertRaises(p.PreprocessingError):
            p.fit_numeric([{"x":None}],"x")
        with self.assertRaises(p.PreprocessingError):
            p.fit_numeric([{"x":float("nan")}],"x")

    def test_pca_optional_real_backend(self):
        try:
            import numpy
        except ImportError:
            with self.assertRaises(p.PreprocessingError):
                p.pca_fit([[1,2],[2,4],[3,6]],1)
        else:
            model=p.pca_fit([[1,2],[2,4],[3,6]],1)
            projection=p.pca_transform([[4,8]],model)
            self.assertEqual(len(projection[0]),1)
            self.assertGreater(model["explained_variance_ratio"][0],.9999)

    def test_bad_pca_model(self):
        with self.assertRaises(p.PreprocessingError):
            p.pca_transform([[1,2]],{"fit_scope":"test_only"})


class SQLiteDataTests(unittest.TestCase):
    def test_key_value_json(self):
        with SQLiteKnowledgeStore() as store:
            store.put_kv("A",{"tag":"T"},"manual")
            self.assertEqual(store.get_kv("A"),{"value":{"tag":"T"},"provenance":"manual"})
            store.put_kv("A",3,"manual")
            self.assertEqual(store.get_kv("A")["value"],3)
            self.assertIsNone(store.get_kv("missing"))

    def test_graph_relations(self):
        with SQLiteKnowledgeStore() as store:
            store.add_relation("A","depends_on","B","doc1")
            store.add_relation("A","depends_on","B","doc2")
            self.assertEqual(store.neighbors("A"),[{"predicate":"depends_on","object":"B","provenance":"doc1"}])

    def test_timeseries(self):
        with SQLiteKnowledgeStore() as store:
            store.add_timeseries("gpu",10,1.5)
            store.add_timeseries("gpu",20,2.5)
            self.assertEqual(len(store.query_timeseries("gpu",15,25)),1)
            with self.assertRaises(sqlite3.IntegrityError):
                store.add_timeseries("gpu",10,2.)

    def test_vectors_cosine(self):
        with SQLiteKnowledgeStore() as store:
            store.put_vector("north",[1,0],"test")
            store.put_vector("east",[0,1],"test")
            store.put_vector("south",[-1,0],"test")
            self.assertEqual([r["key"] for r in store.search_vector([1,0],top_k=3)],
                             ["north","east","south"])

    def test_lineage(self):
        with SQLiteKnowledgeStore() as store:
            ident=store.record_lineage("dataset","features","fit","etl")
            self.assertEqual(store.get_lineage("features")[0]["id"],ident)

    def test_bitemporal_as_known_then(self):
        with SQLiteKnowledgeStore() as store:
            store.add_temporal_fact("state","old",0,100,10)
            store.add_temporal_fact("state","corrected",0,100,20)
            self.assertEqual(store.fact_at("state",50,15)["value"],"old")
            self.assertEqual(store.fact_at("state",50,25)["value"],"corrected")
            self.assertIsNone(store.fact_at("state",110,25))

    def test_bitemporal_tombstone(self):
        with SQLiteKnowledgeStore() as store:
            store.add_temporal_fact("flag",True,0,100,1)
            store.add_temporal_fact("flag",None,0,100,2)
            self.assertIsNone(store.fact_at("flag",50,3))
            self.assertTrue(store.fact_at("flag",50,1)["value"])

    def test_invalid_vector(self):
        with SQLiteKnowledgeStore() as store:
            with self.assertRaises(StoreError):
                store.put_vector("empty",[0,0])
            with self.assertRaises(StoreError):
                store.put_kv("bad",float("nan"))


class MathApiTests(unittest.TestCase):
    def test_stats_dispatch(self):
        answer=calculate({"operation":"statistics.binomial_pmf",
                           "args":{"k":2,"n":3,"p":.5}})
        self.assertAlmostEqual(answer["result"],.375)

    def test_information_dispatch(self):
        answer=calculate({"operation":"information.mutual_information",
                           "args":{"joint":[[.5,0],[0,.5]]}})
        self.assertAlmostEqual(answer["result"],1.)

    def test_preprocessing_dispatch(self):
        answer=calculate({"operation":"preprocessing.fit_numeric",
                           "args":{"rows":[{"x":1},{"x":3}],"column":"x"}})
        self.assertEqual(answer["result"]["mean"],2.)

    def test_invalid_stats_dispatch(self):
        with self.assertRaises(MathAPIError):
            calculate({"operation":"statistics.poisson_pmf","args":{"k":1,"rate":-1}})

    def test_storage_not_exposed_in_untrusted_math_api(self):
        with self.assertRaises(MathAPIError):
            calculate({"operation":"storage.put_kv","args":{}})


if __name__=="__main__":
    unittest.main()

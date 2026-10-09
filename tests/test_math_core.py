"""Mathematical core regression tests (numerical + exact + finite logical)."""
import math
import unittest
from omega_builder.mathematics import linear as l,logic as q,graph as g,probability as p,calculus as c
from omega_builder.mathematics.api import calculate,MathAPIError


class Matrices(unittest.TestCase):
    def assertClose(self,a,b,places=7):
        self.assertEqual(len(a),len(b))
        for row,col in zip(a,b):
            self.assertEqual(len(row),len(col))
            for x,y in zip(row,col):
                self.assertAlmostEqual(x,y,places=places)

    def test_multiply_transpose(self):
        self.assertEqual(l.mmul([[1,2],[3,4]],[[2],[1]]),[[4.],[10.]])
        self.assertEqual(l.transpose([[1,2]]),[[1.],[2.]])

    def test_matrix_elementwise(self):
        self.assertEqual(l.add([[1,2]],[[3,4]]),[[4.,6.]])
        self.assertEqual(l.hadamard([[1,2]],[[3,4]]),[[3.,8.]])

    def test_lu_and_determinant(self):
        a=[[0,2],[3,4]]
        P,L,U=l.lu(a)
        self.assertClose(l.mmul(P,a),l.mmul(L,U))
        self.assertAlmostEqual(l.determinant(a),-6.)

    def test_inverse(self):
        a=[[4,1],[2,3]]
        self.assertClose(l.mmul(a,l.inverse(a)),l.identity(2))

    def test_solve(self):
        x=l.solve([[4,1],[2,3]],[9,8])
        self.assertAlmostEqual(x[0],1.9)
        self.assertAlmostEqual(x[1],1.4)

    def test_qr_householder(self):
        a=[[1,1],[1,0],[0,1]]
        Q,R=l.qr(a)
        self.assertClose(l.mmul(Q,R),a)
        self.assertClose(l.mmul(l.transpose(Q),Q),l.identity(2))

    def test_cholesky(self):
        a=[[4,2],[2,3]]
        low=l.cholesky(a)
        self.assertClose(l.mmul(low,l.transpose(low)),a)

    def test_spd_rejected(self):
        with self.assertRaises(l.MathError):
            l.cholesky([[1,2],[2,1]])

    def test_norm_cosine_cross(self):
        self.assertAlmostEqual(l.norm([3,4]),5.)
        self.assertEqual(l.norm([-3,4],1),7.)
        self.assertEqual(l.norm([-3,4],"inf"),4.)
        self.assertEqual(l.distance([0,0],[3,4],1),7.)
        self.assertAlmostEqual(l.cosine([1,0],[0,1]),0.)
        self.assertEqual(l.cross([1,0,0],[0,1,0]),[0.,0.,1.])

    def test_trace_and_properties(self):
        self.assertEqual(l.trace([[1,2],[3,4]]),5.)
        self.assertTrue(l.diagonal([[1,0],[0,2]]))
        self.assertTrue(l.symmetric([[1,2],[2,3]]))
        self.assertTrue(l.orthogonal([[0,-1],[1,0]]))

    def test_exact_rational_certificate(self):
        o=l.solve_exact([[2,1],[1,-1]],[1,0])
        self.assertEqual(o["solution"],["1/3","1/3"])
        self.assertTrue(o["verified"])
        with self.assertRaises(l.MathError):
            l.solve_exact([[1,1],[2,2]],[1,2])

    def test_bad_input(self):
        with self.assertRaises(l.MathError):
            l.mmul([[1,2]],[[1,2]])
        with self.assertRaises(l.MathError):
            l.mat([[1,2],[3]])
        with self.assertRaises(l.MathError):
            l.vec([True])


class Symbolic(unittest.TestCase):
    def test_tautology(self):
        e=("or",("var","p"),("not",("var","p")))
        o=q.check_validity(e)
        self.assertTrue(o["valid"])
        self.assertEqual(o["assignments_checked"],2)

    def test_counterexample(self):
        o=q.check_validity(("implies",("var","p"),("var","q")))
        self.assertFalse(o["valid"])
        self.assertEqual(o["counterexample"],{"p":True,"q":False})

    def test_entailment(self):
        pre=[("implies",("var","p"),("var","q")),("var","p")]
        self.assertTrue(q.entails(pre,("var","q"))["valid"])

    def test_quantifiers(self):
        self.assertTrue(q.finite_forall([2,4,6],lambda x:x%2==0))
        self.assertTrue(q.finite_exists([1,2,3],lambda x:x==3))

    def test_reject_arbitrary_operator(self):
        with self.assertRaises(q.LogicError):
            q.check_validity(("exec",("var","x")))


class Graphs(unittest.TestCase):
    def test_dijkstra_path(self):
        a={"a":{"b":4,"c":1},"b":{},"c":{"b":1}}
        self.assertEqual(g.dijkstra(a,"a","b"),{"distance":2.,"path":["a","c","b"]})

    def test_topology_and_cycle(self):
        self.assertEqual(g.topological_sort({"a":{"b":1},"b":{}}),["a","b"])
        with self.assertRaises(g.GraphError):
            g.topological_sort({"a":{"b":1},"b":{"a":1}})

    def test_laplacian(self):
        self.assertEqual(g.laplacian({"x":{"y":2},"y":{"x":2}})["matrix"],
                         [[2.,-2.],[-2.,2.]])

    def test_reject_negative_weight(self):
        with self.assertRaises(g.GraphError):
            g.dijkstra({"x":{"x":-1}},"x")


class Statistics(unittest.TestCase):
    def test_bayes(self):
        self.assertAlmostEqual(p.bayes(.5,.8,.2),.8)
        with self.assertRaises(p.ProbabilityError):
            p.bayes(0,0,0)

    def test_entropy_kl(self):
        self.assertAlmostEqual(p.entropy([.5,.5]),1.)
        self.assertAlmostEqual(p.kl([.5,.5],[.5,.5]),0.)
        self.assertTrue(math.isinf(p.kl([1.,0.],[0.,1.])))

    def test_moments(self):
        self.assertAlmostEqual(p.expectation([2,6],[.25,.75]),5.)
        self.assertAlmostEqual(p.variance([2,6],[.25,.75]),3.)
        with self.assertRaises(p.ProbabilityError):
            p.entropy([.9,.9])


class Calculus(unittest.TestCase):
    def test_derivative(self):
        self.assertAlmostEqual(c.derivative(lambda x:x*x,3),6.,places=5)

    def test_gradient_jacobian_hessian(self):
        grad=c.gradient(lambda x:x[0]**2+3*x[1]**2,[2,1])
        self.assertAlmostEqual(grad[0],4.,places=5)
        self.assertAlmostEqual(grad[1],6.,places=5)
        j=c.jacobian(lambda x:[x[0]+x[1],x[0]*x[1]],[2,3])
        self.assertAlmostEqual(j[1][0],3.,places=5)
        h=c.hessian(lambda x:x[0]**2+3*x[1]**2,[2,1])
        self.assertAlmostEqual(h[0][0],2.,places=4)
        self.assertAlmostEqual(h[1][1],6.,places=4)

    def test_integral(self):
        self.assertAlmostEqual(c.integrate_simpson(lambda x:x*x,0,3),9.,places=6)

    def test_descent(self):
        out=c.optimize_descent(lambda x:(x[0]-3)**2,[0.],rate=.2,max_steps=90)
        self.assertLess(out["loss"],1e-7)

    def test_bad_step(self):
        with self.assertRaises(c.CalculusError):
            c.derivative(lambda x:x*x,1.,h=-1)


class Dispatch(unittest.TestCase):
    def test_exact_json(self):
        out=calculate({"operation":"linear.solve_exact","args":{
            "a":[[2,1],[1,-1]],"b":[1,0]}})
        self.assertTrue(out["verified"])

    def test_formula_json(self):
        out=calculate({"operation":"logic.check_validity","args":{
            "formula":["or",["var","p"],["not",["var","p"]]]}})
        self.assertTrue(out["result"]["valid"])

    def test_command_injection_denied(self):
        with self.assertRaises(MathAPIError):
            calculate({"operation":"__import__('os').system","args":{}})


if __name__=="__main__":
    unittest.main()

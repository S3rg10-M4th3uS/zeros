import math
import unittest
from src.comparacao import comparar
from src.exemplos import EXEMPLOS
from src.expressoes import interpretar_expressao
from src.metodos import resolver


class TestesMetodos(unittest.TestCase):
    def test_exemplos_enunciado(self):
        for nome, configuracao in EXEMPLOS.items():
            for resultado in comparar(configuracao):
                with self.subTest(caso=nome, metodo=resultado.metodo):
                    self.assertEqual(resultado.estado, "Convergiu")
                    self.assertLess(resultado.residuo, 1e-6)
                    self.assertAlmostEqual(resultado.raiz, configuracao["referencia"], delta=1e-6)
                    self.assertGreaterEqual(resultado.tempo_us, 0)

    def test_raizes_iniciais(self):
        for metodo in ("bisseccao", "falsa_posicao", "newton", "secante"):
            r = resolver(metodo, lambda x: x, x0=0, derivada=lambda x: 1)
            self.assertEqual((r.raiz, r.iteracoes, r.estado), (0, 0, "Convergiu"))

    def test_extremidade_direita(self):
        for metodo in ("bisseccao", "falsa_posicao"):
            self.assertEqual(resolver(metodo, lambda x: x-1).raiz, 1)

    def test_sem_mudanca_sinal(self):
        for metodo in ("bisseccao", "falsa_posicao"):
            self.assertIn("mudança de sinal", resolver(metodo, lambda x: x*x+1).estado)

    def test_derivada_nula(self):
        self.assertIn("Derivada nula", resolver("newton", lambda x: x*x+1, x0=0,
                                            derivada=lambda x: 2*x).estado)

    def test_valores_iguais_secante(self):
        self.assertIn("divisão por zero", resolver("secante", lambda x: x*x+1, x0=-1, x1=1).estado)

    def test_dominio_e_nao_finitos(self):
        for f in (math.log, lambda x: float("inf"), lambda x: math.exp(1000)):
            self.assertNotEqual(resolver("bisseccao", f).estado, "Convergiu")

    def test_limite_iteracoes(self):
        self.assertEqual(resolver("bisseccao", lambda x: math.cos(x)-x,
                               max_iteracoes=1).estado, "Limite de iterações atingido")

    def test_extrapolacao(self):
        r = resolver("newton", lambda x: x-2, derivada=lambda x: 1)
        self.assertEqual(r.estado, "Convergiu")
        self.assertTrue(r.avisos)

    def test_dominio_fisico(self):
        r = resolver("newton", lambda x: x+1, derivada=lambda x: 1, nao_negativo=True)
        self.assertEqual(r.estado, "Raiz fora do domínio físico")

    def test_estagnacao(self):
        r = resolver("newton", lambda x: 1, x0=1, derivada=lambda x: 1e300)
        self.assertIn("Estagnação", r.estado)

    def test_configuracao_invalida(self):
        for parametros in ({"tolerancia": 0}, {"tolerancia": float("nan")},
                       {"max_iteracoes": 0}, {"a": 1, "b": 0}, {"x0": float("inf")}):
            with self.assertRaises(ValueError):
                resolver("bisseccao", lambda x: x, **parametros)

    def test_descontinuidade_nao_converge(self):
        r = resolver("bisseccao", lambda x: 1/(x-0.5))
        self.assertNotEqual(r.estado, "Convergiu")

    def test_funcao_reescalada(self):
        r = resolver("newton", lambda x: 1e-20*(x-2), derivada=lambda x: 1e-20,
                  tolerancia=1e-25)
        self.assertEqual(r.estado, "Convergiu")


class TestesExpressoes(unittest.TestCase):
    def test_notacao_permitida(self):
        self.assertEqual(interpretar_expressao("t^2 + sen(pi/2)")(3), 10)
        self.assertAlmostEqual(interpretar_expressao("ln(e)")(0), 1)

    def test_rejeita_codigo(self):
        for fonte in ("__import__('os')", "x.real", "[x]", "(lambda: 1)()", "True",
                       "open('arquivo')", "sin(x, x)", "2 if x else 3", "", "x"*501):
            with self.subTest(fonte=fonte), self.assertRaises(ValueError):
                interpretar_expressao(fonte)

    def test_resultado_complexo_falha(self):
        r = resolver("newton", interpretar_expressao("(-1)^0.5"), derivada=lambda x: 1)
        self.assertNotEqual(r.estado, "Convergiu")


if __name__ == "__main__":
    unittest.main()

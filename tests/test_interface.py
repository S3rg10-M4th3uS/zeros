"""Verifica formulários, exemplos, erros e cálculos repetidos no Streamlit."""
from pathlib import Path
import unittest
from streamlit.testing.v1 import AppTest


class TestesInterface(unittest.TestCase):
    def setUp(self):
        self.app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=30).run()

    def enviar(self):
        next(botao for botao in self.app.button if botao.label == "Comparar métodos").click().run()
        self.assertFalse(self.app.exception)

    def test_exemplos_e_limpeza(self):
        for nome in list(self.app.selectbox[0].options)[:3]:
            self.app.selectbox[0].select(nome).run()
            self.enviar()
            self.assertEqual(len(self.app.dataframe[0].value), 4)
            self.assertTrue((self.app.dataframe[0].value["Estado"] == "Convergiu").all())
        next(botao for botao in self.app.button if botao.label == "Limpar resultados").click().run()
        self.assertFalse(self.app.exception)
        self.assertEqual(len(self.app.dataframe), 0)

    def test_expressao_invalida_e_recuperacao(self):
        self.app.text_input[0].set_value("__import__('os')")
        self.enviar()
        self.assertTrue(self.app.error)
        self.app.text_input[0].set_value("cos(x)-x")
        self.enviar()
        self.assertFalse(self.app.error)
        self.assertEqual(len(self.app.dataframe[0].value), 4)

    def test_funcao_personalizada(self):
        self.app.selectbox[0].select("Função personalizada").run()
        self.enviar()
        self.assertTrue((self.app.dataframe[0].value["Estado"] == "Convergiu").all())


if __name__ == "__main__":
    unittest.main()

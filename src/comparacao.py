"""Executa todos os métodos com a mesma tolerância e limite de iterações."""
from .expressoes import interpretar_expressao
from .metodos import resolver


def comparar(configuracao, tolerancia=1e-6, max_iteracoes=100):
    # Interpreta as entradas uma vez, fora do tempo medido por cada método.
    f = interpretar_expressao(configuracao["expressao"])
    derivada = interpretar_expressao(configuracao["derivada"])
    resultados = []
    # A ordem fixa mantém tabelas, gráficos e amostras temporais alinhados.
    # Somente a Secante usa secante_x0; Newton usa a estimativa x0.
    for metodo in ("bisseccao", "falsa_posicao", "newton", "secante"):
        resultados.append(resolver(metodo, f, a=configuracao["a"], b=configuracao["b"],
            x0=configuracao["secante_x0"] if metodo == "secante" else configuracao["x0"],
            x1=configuracao["x1"], derivada=derivada, tolerancia=tolerancia,
            max_iteracoes=max_iteracoes, nao_negativo=configuracao.get("nao_negativo", False)))
    return resultados


# Converte os resultados para o formato comum da interface e da exportação CSV.
def linhas(resultados):
    return [{"Método": r.metodo, "Raiz": r.raiz, "Iterações": r.iteracoes,
             "Tempo (µs)": r.tempo_us, "Resíduo |f(x)|": r.residuo,
             "Estado": r.estado} for r in resultados]

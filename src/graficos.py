"""Gráficos compartilhados pela interface e pelo relatório gerado."""
import matplotlib
# O backend Agg gera imagens sem exigir uma janela gráfica no computador.
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from .expressoes import interpretar_expressao
from .metodos import valor_finito, FalhaNumerica


def criar_graficos(configuracao, resultados, tolerancia):
    f = interpretar_expressao(configuracao["expressao"])
    a, b = configuracao["a"], configuracao["b"]
    # Amostra 601 pontos no intervalo informado. O desenho não comprova
    # continuidade e pode não revelar detalhes entre dois pontos consecutivos.
    valores_x = [(1 - i/600)*a + (i/600)*b for i in range(601)]
    valores_y = []
    for x in valores_x:
        try:
            valores_y.append(valor_finito(f, x))
        except FalhaNumerica:
            # NaN deixa uma lacuna no gráfico onde a avaliação falhou.
            valores_y.append(float("nan"))
    figura_funcao, eixo = plt.subplots(figsize=(8, 3.6), layout="constrained")
    eixo.plot(valores_x, valores_y, label="f(x)", color="#2563eb")
    eixo.axhline(0, color="#64748b", linewidth=0.8)
    for resultado in resultados:
        # Aproximações de execuções que falharam não são marcadas como raízes.
        if resultado.estado == "Convergiu":
            eixo.scatter([resultado.raiz], [f(resultado.raiz)], label=resultado.metodo, s=40)
    eixo.set(xlabel="t" if configuracao.get("nao_negativo") else "x", ylabel="f(x)",
           title="Função e raízes aproximadas")
    eixo.grid(alpha=0.2)
    eixo.legend(fontsize=8)
    figura_convergencia, eixo = plt.subplots(figsize=(8, 3.6), layout="constrained")
    for resultado in resultados:
        if resultado.historico:
            # A escala logarítmica evidencia as ordens de grandeza dos resíduos.
            # O piso evita log(0) apenas no desenho; o histórico mantém o valor real.
            eixo.semilogy([s.iteracao for s in resultado.historico],
                        [max(s.residuo, 1e-300) for s in resultado.historico],
                        marker=".", label=resultado.metodo)
    eixo.axhline(tolerancia, linestyle="--", color="#64748b", label="Tolerância")
    eixo.set(xlabel="Iteração (0 = dados iniciais)", ylabel="Resíduo |f(x)|",
           title="Convergência dos métodos")
    eixo.grid(alpha=0.2)
    eixo.legend(fontsize=8)
    return figura_funcao, figura_convergencia

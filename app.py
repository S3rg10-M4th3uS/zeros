"""Execute com: streamlit run app.py."""
from dataclasses import asdict
import json
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from src.comparacao import comparar, linhas
from src.exemplos import EXEMPLOS
from src.graficos import criar_graficos

st.set_page_config(page_title="Zeros · Cálculo Numérico", page_icon="📈", layout="wide")
st.title("Zeros de funções")
st.caption("Cálculo Numérico · Unidade 1 · 2026.2")
st.write("Compare Bissecção, Falsa Posição, Newton-Raphson e Secante usando o mesmo critério de parada.")
escolha = st.selectbox("Problema", [*EXEMPLOS, "Função personalizada"])
base = EXEMPLOS.get(escolha, dict(expressao="x^3-x-2", derivada="3*x^2-1",
    a=1.0, b=2.0, x0=1.5, secante_x0=1.0, x1=2.0, nao_negativo=False))
# O formulário envia os campos juntos ao clicar em comparar. Uma chave por
# problema permite carregar os valores iniciais correspondentes à seleção.
with st.form(f"inputs_{escolha}"):
    esquerda, direita = st.columns(2)
    expressao = esquerda.text_input("Função f(x) ou f(t)", base["expressao"])
    derivada = direita.text_input("Derivada para Newton", base["derivada"])
    st.caption("Use * para multiplicação, ponto decimal e ^ ou ** para potência. Funções: sin/sen, cos, tan, exp, log/ln, log10, sqrt, abs, sinh, cosh, tanh, asin, acos, atan. Constantes: pi, e.")
    c1, c2, c3 = st.columns(3)
    a = c1.number_input("Extremidade a", value=base["a"], format="%.10f")
    b = c2.number_input("Extremidade b", value=base["b"], format="%.10f")
    x0 = c3.number_input("Newton: estimativa inicial", value=base["x0"], format="%.10f")
    c1, c2, c3 = st.columns(3)
    secante_x0 = c1.number_input("Secante: primeira estimativa", value=base["secante_x0"], format="%.10f")
    x1 = c2.number_input("Secante: segunda estimativa", value=base["x1"], format="%.10f")
    tolerancia = c3.number_input("Tolerância residual ε", value=1e-6, format="%.2e")
    max_iteracoes = st.number_input("Máximo de iterações", min_value=1, max_value=100000, value=100)
    nao_negativo = st.checkbox("Problema físico: exigir raiz t ≥ 0", value=base["nao_negativo"])
    enviado = st.form_submit_button("Comparar métodos", type="primary")
if enviado:
    configuracao = dict(expressao=expressao, derivada=derivada, a=a, b=b, x0=x0,
                  secante_x0=secante_x0, x1=x1, nao_negativo=nao_negativo)
    try:
        resultados = comparar(configuracao, tolerancia, int(max_iteracoes))
        # Streamlit reexecuta o script nas interações. A sessão conserva os
        # resultados e as entradas efetivamente usadas até o próximo cálculo.
        st.session_state["calculo"] = (escolha, configuracao, tolerancia, max_iteracoes, resultados)
    except (ValueError, OverflowError) as erro:
        # Remove resultados antigos para não associá-los a uma entrada inválida.
        st.session_state.pop("calculo", None)
        st.error(str(erro))
def limpar_resultados():
    st.session_state.pop("calculo", None)


# O callback limpa a sessão antes de a página ser renderizada novamente.
st.button("Limpar resultados", on_click=limpar_resultados)
if "calculo" in st.session_state:
    titulo, configuracao, tolerancia_usada, limite, resultados = st.session_state["calculo"]
    st.subheader("Resultado da última execução")
    st.caption(f"{titulo} · f = {configuracao['expressao']} · ε = {tolerancia_usada:g} · máximo = {limite}. Alterou os campos? Clique em Comparar métodos para atualizar.")
    st.caption(f"Intervalo: [{configuracao['a']:g}, {configuracao['b']:g}] · Newton: {configuracao['x0']:g} · Secante: {configuracao['secante_x0']:g}, {configuracao['x1']:g} · Derivada: {configuracao['derivada']}")
    # A formatação arredonda só a exibição; os dados exportados mantêm os floats.
    tabela = pd.DataFrame(linhas(resultados))
    st.dataframe(tabela.style.format({"Raiz": "{:.12g}", "Tempo (µs)": "{:.3f}",
                                    "Resíduo |f(x)|": "{:.3e}"}, na_rep="—"), hide_index=True, width="stretch")
    st.caption("Sucesso: |f(x)| < ε. Resíduo não é o erro absoluto da raiz. Tempo inclui cálculo e histórico, excluindo leitura da expressão e gráficos; medições curtas variam entre execuções.")
    for resultado in resultados:
        if resultado.estado != "Convergiu":
            st.warning(f"{resultado.metodo}: {resultado.estado}")
        for aviso in resultado.avisos:
            st.warning(f"{resultado.metodo}: {aviso}")
    for figura in criar_graficos(configuracao, resultados, tolerancia_usada):
        st.pyplot(figura)
        # Libera a figura após exibi-la, evitando acumular memória nas interações.
        plt.close(figura)
    st.caption("O gráfico amostra pontos no intervalo informado; não prova continuidade nem a existência de todas as raízes. Métodos abertos podem encontrar raízes fora desse intervalo.")
    with st.expander("Histórico das aproximações"):
        for resultado in resultados:
            st.write(resultado.metodo)
            st.dataframe(pd.DataFrame([asdict(passo) for passo in resultado.historico]).rename(columns={
                "iteracao": "Iteração", "x": "Aproximação", "residuo": "Resíduo", "variacao": "Variação em x"}), hide_index=True)
    c1, c2 = st.columns(2)
    # UTF-8 com BOM facilita abrir os acentos do CSV em programas de planilhas.
    c1.download_button("Baixar tabela CSV", tabela.to_csv(index=False).encode("utf-8-sig"), "resultados.csv", "text/csv")
    # O JSON inclui parâmetros e históricos para permitir reproduzir a análise.
    conteudo = dict(problema=titulo, configuracao=configuracao, tolerancia=tolerancia_usada, max_iteracoes=limite,
                   resultados=[asdict(resultado) for resultado in resultados])
    c2.download_button("Baixar dados e históricos JSON", json.dumps(conteudo, ensure_ascii=False, indent=2), "resultados.json", "application/json")
with st.expander("Como interpretar os métodos"):
    st.write("Bissecção e Falsa Posição exigem mudança de sinal e continuidade da função no intervalo. A interface verifica os sinais; a continuidade deve ser analisada por quem define a função. A Falsa Posição implementada é a versão clássica.")
    st.write("Newton usa a derivada informada; uma derivada incorreta pode comprometer a convergência. Secante usa duas aproximações. Ambos podem extrapolar o intervalo, encontrar outra raiz ou falhar.")
    st.write("Uma raiz presente nos dados iniciais exige zero iterações. Cada tentativa de atualização conta uma iteração, inclusive se falhar. A Secante tem duas amostras iniciais na iteração zero.")
st.caption("Para encerrar: feche esta aba e pressione Ctrl+C no terminal que iniciou o Streamlit.")

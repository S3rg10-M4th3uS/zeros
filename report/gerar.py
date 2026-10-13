"""Gera dados reproduzíveis, Markdown, gráficos e relatório PDF.

Execute na raiz do projeto: python -m report.gerar
"""
from dataclasses import asdict
from datetime import datetime, timezone
import csv
import json
from pathlib import Path
import platform
from statistics import median
from xml.sax.saxutils import escape
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from src.comparacao import comparar, linhas
from src.exemplos import EXEMPLOS
from src.graficos import criar_graficos

SAIDA = Path(__file__).resolve().parent
REPETICOES = 31
ANALISES = [
    "Newton convergiu em 3 atualizações, Secante em 4, Falsa Posição em 5 e Bissecção em 20. "
    "As estimativas iniciais favorecem os métodos abertos nesta função suave. A derivada -sin(x)-1 "
    "não se anula em [0,1]. A Bissecção reduz o intervalo pela metade a cada passo e exige mais atualizações, "
    "mas mantém o confinamento da raiz. A referência decimal serve para validação independente.",
    "Newton convergiu em 5 atualizações e Secante em 6, contra 21 da Falsa Posição e 25 da Bissecção. "
    "A Falsa Posição conserva uma extremidade por vários passos nesta curva exponencial, limitando seu avanço. "
    "Da equação 90 exp(-0.15t)=30 resulta t=ln(3)/0.15, aproximadamente 7.3240819245 minutos. "
    "O componente esfria de 110 °C em direção a 20 °C; o instante calculado marca a passagem por 50 °C. "
    "A função é estritamente decrescente, portanto essa raiz é única para t >= 0.",
    "Newton convergiu em 5 atualizações, Secante em 6, Bissecção em 18 e Falsa Posição em 23. "
    "A Falsa Posição clássica foi mais lenta em iterações que a Bissecção: interpolar não garante avanço "
    "mais rápido quando uma extremidade permanece fixa. A solução analítica é t=-ln(0.24), aproximadamente "
    "1.4271163556 segundos. O modelo fornecido corresponde à carga até 5 V com constante de tempo de 1 s. "
    "O instante de cruzamento de um limiar de tensão permite estudar atrasos em temporizadores, tempo de "
    "acomodação de sinais de sensores e decisões de leitura em sistemas embarcados."
]


def principal():
    estilos = getSampleStyleSheet()
    estilos["Normal"].fontSize = 10
    estilos["Normal"].leading = 14
    # Mantém apresentações PDF/Markdown e dados brutos da mesma execução.
    elementos, markdown, casos = [], [], []

    def paragrafo(texto, titulo_secao=False):
        # Escape protege símbolos como < para não virarem marcação do ReportLab.
        elementos.append(Paragraph(escape(texto), estilos["Heading2" if titulo_secao else "Normal"]))
        elementos.append(Spacer(1, 0.15*cm))
        markdown.append(("## " if titulo_secao else "") + texto + "\n")

    paragrafo("Comparativo de métodos para zeros de funções", True)
    paragrafo("Cálculo Numérico — Unidade 1 — 2026.2")
    # Autoria vem de um arquivo editável; contribuições não são inferidas.
    equipe = json.loads((SAIDA / "equipe.json").read_text())
    if not 1 <= len(equipe) <= 3:
        raise ValueError("Informe de 1 a 3 integrantes em report/equipe.json.")
    if any(integrante["nome"] == "A preencher" for integrante in equipe):
        paragrafo("VERSÃO PARA REVISÃO: preencher nomes e contribuições reais em report/equipe.json e gerar novamente antes da entrega.")
    paragrafo("Programa e execução", True)
    paragrafo("O simulador implementa Bissecção, Falsa Posição clássica, Newton-Raphson e Secante em Python. "
              "A interface Streamlit aceita funções personalizadas, estimativas, tolerância e limite de iterações. "
              "Apresenta tabela, gráficos, histórico e exportação CSV/JSON. O interpretador de expressões permite "
              "apenas operações matemáticas autorizadas, sem executar código Python arbitrário.")
    paragrafo("Instale as dependências de requirements.txt em um ambiente virtual Python 3.13, conforme o README. Na pasta do projeto: python -m streamlit run app.py. "
              "Abra o endereço local apresentado, escolha um exemplo e clique em Comparar métodos. "
              "Para novos cálculos, altere as entradas e execute novamente; para encerrar, feche a aba e use Ctrl+C no terminal. "
              "Testes: python -m unittest discover -s tests -v. "
              "Relatório: python -m report.gerar.")
    paragrafo("Métodos e condições de convergência", True)
    paragrafo("Bissecção: c=(a+b)/2, conservando a metade com mudança de sinal. Falsa Posição: "
              "c=(a f(b)-b f(a))/(f(b)-f(a)), conservando o subintervalo com mudança de sinal. "
              "Ambos pressupõem continuidade. A verificação dos sinais não comprova essa hipótese. "
              "A implementação da Falsa Posição usa uma expressão equivalente com pesos normalizados para evitar overflow.")
    paragrafo("Newton: x seguinte = x - f(x)/f'(x). Secante: x seguinte = x1 - f(x1)(x1-x0)/(f(x1)-f(x0)). "
              "Newton tem convergência local quadrática para uma raiz simples sob as condições usuais de suavidade "
              "e estimativa inicial adequada; Secante tem ordem local aproximadamente 1.618. Bissecção é linear "
              "e Falsa Posição clássica pode ser lenta. Métodos abertos não garantem permanecer no intervalo.")
    paragrafo("Protocolo de comparação", True)
    paragrafo("Todos os casos usam |f(x)| < 1e-6 e no máximo 100 iterações. Precisão final é reportada como "
              "resíduo, não como garantia de erro absoluto em x. Também é informado o erro frente à referência. "
              "Dados iniciais que já satisfazem o critério contam como zero iterações. Cada tentativa de atualização "
              "conta uma iteração; as duas sementes da Secante aparecem no histórico na iteração zero.")
    paragrafo(f"Tempos em microssegundos são medianas de {REPETICOES} execuções, após uma execução de aquecimento. "
              "A medição usa perf_counter_ns e inclui avaliações e armazenamento do histórico; exclui análise "
              "da expressão, interface e gráficos. O JSON inclui cada amostra temporal. A tabela da interface "
              "mostra o tempo de uma única execução. Tempos tão curtos dependem do ambiente e não estabelecem "
              "um vencedor universal; a análise prioriza convergência, iterações e resíduos.")
    metadados = dict(gerado_em=datetime.now(timezone.utc).isoformat(), python=platform.python_version(),
                    plataforma=platform.platform(), repeticoes=REPETICOES, tolerancia=1e-6, max_iteracoes=100)
    paragrafo(f"Ambiente de medição: Python {metadados['python']}; {metadados['plataforma']}. "
              f"Gerado em UTC: {metadados['gerado_em']}.")
    for indice, (nome, configuracao) in enumerate(EXEMPLOS.items()):
        comparar(configuracao)  # Aquece a execução antes de coletar as medições.
        execucoes = [comparar(configuracao) for _ in range(REPETICOES)]
        # A última execução fornece raízes e históricos. Somente o tempo
        # é substituído pela mediana das repetições, menos sensível a picos.
        resultados = execucoes[-1]
        # Guarda também os tempos individuais para permitir conferir a mediana.
        amostras = {r.metodo: [execucao[i].tempo_us for execucao in execucoes] for i, r in enumerate(resultados)}
        for r in resultados:
            r.tempo_us = median(amostras[r.metodo])
            # Impede publicar uma demonstração como concluída se o cálculo falhar.
            if r.estado != "Convergiu" or r.residuo >= 1e-6:
                raise RuntimeError(f"Demonstração falhou: {nome}, {r.metodo}: {r.estado}")
        elementos.append(PageBreak())
        paragrafo(nome, True)
        paragrafo(f"f = {configuracao['expressao']}; derivada = {configuracao['derivada']}. "
                  f"Intervalo [{configuracao['a']:g}, {configuracao['b']:g}]; Newton x0={configuracao['x0']:g}; "
                  f"Secante x0={configuracao['secante_x0']:g}, x1={configuracao['x1']:g}. "
                  f"Referência: {configuracao['referencia']:.12g} {configuracao['unidade']}.")
        dados = [["Método", "Raiz", "Iter.", "Tempo (µs)", "|f(raiz)|"]]
        for r in resultados:
            dados.append([r.metodo, f"{r.raiz:.12g}", str(r.iteracoes),
                         f"{r.tempo_us:.3f}", f"{r.residuo:.3e}"])
        tabela = Table(dados, colWidths=[3.5*cm, 3.4*cm, 1.3*cm, 2.7*cm, 2.7*cm])
        tabela.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dbeafe")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.lightgrey)]))
        elementos.extend([tabela, Spacer(1, 0.25*cm)])
        # Escapa as barras de |f(raiz)|, pois | separa colunas no Markdown.
        markdown.extend(["| " + " | ".join(celula.replace("|", "\\|") for celula in dados[0]) + " |", "|---|---|---|---|---|"])
        markdown.extend("| " + " | ".join(linha) + " |" for linha in dados[1:])
        markdown.append("")
        paragrafo(ANALISES[indice])
        paragrafo("Erro absoluto frente à referência: " + "; ".join(
            f"{r.metodo}: {abs(r.raiz-configuracao['referencia']):.3e}" for r in resultados) + ".")
        avisos = [f"{r.metodo}: {w}" for r in resultados for w in r.avisos]
        paragrafo("Não houve falhas por derivada nula, denominador nulo ou falta de mudança de sinal. " +
                  (" ".join(avisos) if avisos else "Não houve extrapolação do intervalo nesta execução."))
        # Reutiliza os gráficos da interface para manter a apresentação coerente.
        for indice_grafico, figura in enumerate(criar_graficos(configuracao, resultados, 1e-6)):
            nome_arquivo = f"caso_{indice+1}_{indice_grafico+1}.png"
            figura.savefig(SAIDA / nome_arquivo, dpi=140)
            plt.close(figura)
            elementos.append(Image(str(SAIDA / nome_arquivo), width=15*cm, height=6.75*cm))
            markdown.append(f"![Gráfico]({nome_arquivo})\n")
        casos.append(dict(nome=nome, configuracao=configuracao, resultados=[asdict(r) for r in resultados], amostras_tempo_us=amostras))
    elementos.append(PageBreak())
    paragrafo("Análise crítica e limitações", True)
    paragrafo("Newton foi o mais eficiente em número de atualizações nos três casos escolhidos. Isso depende "
              "de boas estimativas e de uma derivada disponível e correta. Cada atualização de Newton avalia "
              "também a derivada, portanto menos iterações não implica automaticamente menor tempo. Secante "
              "ofereceu uma alternativa rápida sem derivada. Os métodos de intervalo mantiveram a raiz "
              "confinada; a Falsa Posição não superou a Bissecção em todos os exemplos.")
    paragrafo("As dificuldades tratadas foram distinguir resíduo de erro na raiz, evitar que estagnação "
              "fosse considerada sucesso, validar domínio e expressões, e comparar tempos curtos. "
              "Os testes exercitam derivada nula, valores iguais na Secante, ausência de mudança de sinal, "
              "função indefinida, valores não finitos, limite de iterações, estagnação e extrapolação. "
              "Derivadas pequenas não são rejeitadas por um limiar absoluto arbitrário, que dependeria "
              "da escala de f; o programa verifica denominador zero, resultados não finitos e convergência.")
    paragrafo("O programa não comprova continuidade nem correção da derivada fornecida. Os gráficos são "
              "amostragens e podem não revelar descontinuidades. O erro em ponto flutuante e estimativas "
              "desfavoráveis podem impedir a convergência. A indicação de domínio físico t >= 0 rejeita "
              "uma raiz negativa e registra aproximações negativas, sem alterar as fórmulas dos métodos.")
    paragrafo("Escopo adotado", True)
    paragrafo("O enunciado alterna entre escolher um problema de engenharia e apresentar ambos; foram "
              "incluídos os dois e o caso de validação. As menções a truncamento e arredondamento na "
              "rubrica parecem pertencer à atividade de propagação de erros: não foi criado um simulador "
              "separado desse tema. Os cálculos usam ponto flutuante e apenas a apresentação arredonda os valores.")
    paragrafo("Participação dos integrantes", True)
    for integrante in equipe:
        paragrafo(f"{integrante['nome']}: {integrante['contribuicao']}")
    paragrafo("Material de referência", True)
    paragrafo("Enunciado fornecido da disciplina Cálculo Numérico, Projeto Unidade 1 (Zeros), 2026.2. "
              "Os resultados e gráficos foram gerados pelo código deste projeto; consultar README.md para reprodução.")

    def rodape(tela, documento):
        tela.setFont("Helvetica", 9)
        tela.drawRightString(19*cm, 1*cm, f"Zeros | {documento.page}")

    SimpleDocTemplate(str(SAIDA / "relatorio.pdf"), title="Comparativo de métodos para zeros de funções",
                      leftMargin=2*cm, rightMargin=2*cm, topMargin=1.7*cm, bottomMargin=1.7*cm).build(
                          elementos, onFirstPage=rodape, onLaterPages=rodape)
    (SAIDA / "relatorio.md").write_text("\n".join(markdown), encoding="utf-8")
    # Exporta valores numéricos completos, além das tabelas arredondadas do PDF.
    (SAIDA / "resultados.json").write_text(json.dumps(dict(metadados=metadados, casos=casos), ensure_ascii=False, indent=2), encoding="utf-8")
    with (SAIDA / "resultados.csv").open("w", newline="", encoding="utf-8-sig") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=["Problema", *linhas(resultados)[0]])
        escritor.writeheader()
        for caso in casos:
            for resultado in caso["resultados"]:
                escritor.writerow({"Problema": caso["nome"], "Método": resultado["metodo"], "Raiz": resultado["raiz"],
                    "Iterações": resultado["iteracoes"], "Tempo (µs)": resultado["tempo_us"],
                    "Resíduo |f(x)|": resultado["residuo"], "Estado": resultado["estado"]})
    print(f"Relatório e dados gerados em {SAIDA}")


if __name__ == "__main__":
    principal()

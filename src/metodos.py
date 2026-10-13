"""Métodos clássicos com critério residual comum e falhas explícitas."""
from dataclasses import dataclass, field
import math
from time import perf_counter_ns


@dataclass
# Cada passo preserva o resíduo e a variação em x para a tabela e o gráfico.
# A variação é informativa: o sucesso depende do resíduo, não do tamanho do passo.
class Passo:
    iteracao: int
    x: float
    residuo: float
    variacao: float | None = None


@dataclass
# Um resultado também representa falhas; raiz e resíduo podem ficar sem valor
# quando nenhuma avaliação válida foi obtida.
class Resultado:
    metodo: str
    raiz: float | None = None
    residuo: float | None = None
    iteracoes: int = 0
    tempo_us: float = 0.0
    estado: str = ""
    # Cada execução recebe listas próprias, evitando misturar históricos e avisos.
    historico: list[Passo] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)


class FalhaNumerica(Exception):
    """Falha numérica esperada, apresentada ao usuário sem rastreamento de exceção."""


def valor_finito(f, x):
    # Impede que infinito ou NaN contaminem as próximas operações do algoritmo.
    if not math.isfinite(x):
        raise FalhaNumerica("A aproximação deixou de ser finita.")
    # Domínio inválido, overflow e resultados complexos viram falhas numéricas
    # que a interface pode explicar sem interromper a comparação dos métodos.
    try:
        valor = float(f(x))
    except (ArithmeticError, ValueError, TypeError) as erro:
        raise FalhaNumerica(f"Função indefinida em x={x:.8g}: {erro}") from erro
    if not math.isfinite(valor):
        raise FalhaNumerica(f"Função não finita em x={x:.8g}.")
    return valor


def resolver(metodo, f, *, a=0.0, b=1.0, x0=0.5, x1=1.0, derivada=None,
          tolerancia=1e-6, max_iteracoes=100, nao_negativo=False):
    """Mede o cálculo numérico e o histórico, excluindo interpretação e gráficos.

    Raízes iniciais contam como zero iterações. Cada atualização tentada conta uma.
    Métodos abertos podem sair de [a,b]; o evento é registrado, sem limitar o passo.
    """
    nomes = {"bisseccao": "Bissecção", "falsa_posicao": "Falsa Posição",
             "newton": "Newton-Raphson", "secante": "Secante"}
    if metodo not in nomes:
        raise ValueError("Método desconhecido.")
    # Configurações inválidas são rejeitadas antes de iniciar a cronometragem.
    if not math.isfinite(tolerancia) or tolerancia <= 0:
        raise ValueError("A tolerância deve ser positiva e finita.")
    if type(max_iteracoes) is not int or not 1 <= max_iteracoes <= 100000:
        raise ValueError("O limite deve ser um inteiro entre 1 e 100000.")
    if not all(math.isfinite(v) for v in (a, b, x0, x1)) or a >= b:
        raise ValueError("Use estimativas finitas e um intervalo com a < b.")
    resultado = Resultado(nomes[metodo])
    # O relógio mede somente a resolução, incluindo avaliações e histórico.
    inicio = perf_counter_ns()

    # Centraliza o registro e o critério de parada para que todos os métodos
    # adotem a mesma definição de convergência.
    def registrar(x, fx, anterior=None):
        resultado.raiz, resultado.residuo = x, abs(fx)
        resultado.historico.append(Passo(resultado.iteracoes, x, abs(fx),
                                   None if anterior is None else abs(x - anterior)))
        # Os métodos abertos podem extrapolar; limitar x mudaria suas fórmulas.
        # O aviso é guardado uma única vez, mesmo se o evento se repetir.
        if metodo in ("newton", "secante") and not a <= x <= b:
            aviso = "Houve aproximação fora do intervalo de referência."
            if aviso not in resultado.avisos:
                resultado.avisos.append(aviso)
        if nao_negativo and x < 0:
            aviso = "Houve aproximação negativa, fora do domínio físico t ≥ 0."
            if aviso not in resultado.avisos:
                resultado.avisos.append(aviso)
        # Resíduo pequeno significa f(x) próximo de zero; não garante, por si só,
        # que a distância de x à raiz verdadeira seja menor que a tolerância.
        if abs(fx) < tolerancia:
            resultado.estado = ("Raiz fora do domínio físico" if nao_negativo and x < 0 else "Convergiu")
            return True
        return False

    try:
        if metodo in ("bisseccao", "falsa_posicao"):
            esquerda, direita = a, b
            f_esquerda, f_direita = valor_finito(f, esquerda), valor_finito(f, direita)
            # Verifica as extremidades antes de exigir mudança de sinal.
            # Uma aproximação inicial aceitável encerra com zero iterações.
            if abs(f_esquerda) < tolerancia:
                registrar(esquerda, f_esquerda)
                return resultado
            if abs(f_direita) < tolerancia:
                registrar(direita, f_direita)
                return resultado
            # Comparar sinais diretamente evita overflow no produto f(a)*f(b).
            if (f_esquerda > 0) == (f_direita > 0):
                raise FalhaNumerica("Ausência de mudança de sinal no intervalo.")
            anterior = None
            for iteracao in range(1, max_iteracoes + 1):
                resultado.iteracoes = iteracao
                if metodo == "bisseccao":
                    # Ponto médio: dividir antes de somar reduz o risco de overflow.
                    x = esquerda / 2 + direita / 2
                else:
                    # Magnitudes normalizadas evitam overflow na interpolação da Falsa Posição.
                    # Para sinais opostos, peso = |f(a)| / (|f(a)| + |f(b)|).
                    # A combinação abaixo é equivalente à interseção da reta com y=0.
                    escala = max(abs(f_esquerda), abs(f_direita))
                    peso = (abs(f_esquerda) / escala) / (abs(f_esquerda) / escala + abs(f_direita) / escala)
                    x = (1 - peso) * esquerda + peso * direita
                fx = valor_finito(f, x)
                if registrar(x, fx, anterior):
                    break
                # Se o arredondamento impede novos avanços sem satisfazer o resíduo,
                # a execução estagnou e não deve ser declarada convergente.
                if x == anterior or x == esquerda or x == direita:
                    raise FalhaNumerica("Estagnação sem atingir a tolerância residual.")
                # Mantém o subintervalo cujas extremidades têm sinais opostos.
                if (f_esquerda > 0) != (fx > 0):
                    direita, f_direita = x, fx
                else:
                    esquerda, f_esquerda = x, fx
                anterior = x
        else:
            atual = x0
            f_atual = valor_finito(f, atual)
            if registrar(atual, f_atual):
                return resultado
            anterior = None
            # Newton começa com uma semente; Secante precisa de duas avaliações.
            # As sementes da Secante pertencem à iteração zero do histórico.
            if metodo == "secante":
                anterior, f_anterior = atual, f_atual
                atual = x1
                f_atual = valor_finito(f, atual)
                if registrar(atual, f_atual, anterior):
                    return resultado
            elif derivada is None:
                raise FalhaNumerica("Informe a derivada para Newton-Raphson.")
            for iteracao in range(1, max_iteracoes + 1):
                resultado.iteracoes = iteracao
                if metodo == "newton":
                    inclinacao = valor_finito(derivada, atual)
                    # Não se usa um limiar absoluto para derivada pequena: reescalar
                    # f também reescala f', sem necessariamente prejudicar Newton.
                    if inclinacao == 0:
                        raise FalhaNumerica("Derivada nula: divisão por zero em Newton.")
                    # Interseção da tangente em x atual com o eixo horizontal.
                    candidato = atual - f_atual / inclinacao
                else:
                    # A Secante estima a inclinação usando as duas últimas amostras.
                    denominador = f_atual - f_anterior
                    if denominador == 0:
                        raise FalhaNumerica("Valores de função iguais: divisão por zero na Secante.")
                    candidato = atual - (f_atual / denominador) * (atual - anterior)
                valor = valor_finito(f, candidato)
                if registrar(candidato, valor, atual):
                    break
                if candidato == atual:
                    raise FalhaNumerica("Estagnação sem atingir a tolerância residual.")
                # Reaproveita a avaliação anterior; a Secante não recalcula f(x)
                # para as aproximações que já conhece.
                anterior, f_anterior = atual, f_atual
                atual, f_atual = candidato, valor
        # Chegar ao fim do laço sem sucesso é diferente de encontrar uma raiz.
        if not resultado.estado:
            resultado.estado = "Limite de iterações atingido"
    # Preserva a última aproximação válida, acompanhada do motivo da falha.
    except FalhaNumerica as erro:
        resultado.estado = str(erro)
    except (ArithmeticError, ValueError) as erro:
        resultado.estado = f"Falha aritmética: {erro}"
    finally:
        # O finally também é executado nos retornos antecipados e nas falhas.
        # perf_counter_ns fornece nanossegundos; dividir por 1000 produz µs.
        resultado.tempo_us = (perf_counter_ns() - inicio) / 1000
    return resultado

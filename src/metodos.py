"""Métodos clássicos com critério residual comum e falhas explícitas.

Organização do arquivo:
  1. Estruturas de dados (Passo, Resultado, FalhaNumerica).
  2. Utilitários comuns (valor_finito, Registro).
  3. Os quatro métodos, cada um em sua própria função:
       - bisseccao
       - falsa_posicao
       - newton_raphson
       - secante
  4. resolver: valida a configuração, cronometra e chama o método escolhido.
"""
from dataclasses import dataclass, field
import math
from time import perf_counter_ns


# =============================================================================
# 1. Estruturas de dados
# =============================================================================

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


# =============================================================================
# 2. Utilitários comuns a todos os métodos
# =============================================================================

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


class Registro:
    """Centraliza o registro e o critério de parada para que todos os métodos
    adotem a mesma definição de convergência."""

    def __init__(self, resultado, *, tolerancia, a, b, nao_negativo, metodo_aberto):
        self.resultado = resultado
        self.tolerancia = tolerancia
        self.a, self.b = a, b
        self.nao_negativo = nao_negativo
        self.metodo_aberto = metodo_aberto

    def nova_iteracao(self, iteracao):
        self.resultado.iteracoes = iteracao

    def _avisar(self, aviso):
        # O aviso é guardado uma única vez, mesmo se o evento se repetir.
        if aviso not in self.resultado.avisos:
            self.resultado.avisos.append(aviso)

    def registrar(self, x, fx, anterior=None):
        """Guarda o passo no histórico e devolve True se |f(x)| < tolerância."""
        r = self.resultado
        r.raiz, r.residuo = x, abs(fx)
        r.historico.append(Passo(r.iteracoes, x, abs(fx),
                                 None if anterior is None else abs(x - anterior)))
        # Os métodos abertos podem extrapolar; limitar x mudaria suas fórmulas.
        if self.metodo_aberto and not self.a <= x <= self.b:
            self._avisar("Houve aproximação fora do intervalo de referência.")
        if self.nao_negativo and x < 0:
            self._avisar("Houve aproximação negativa, fora do domínio físico t ≥ 0.")
        # Resíduo pequeno significa f(x) próximo de zero; não garante, por si só,
        # que a distância de x à raiz verdadeira seja menor que a tolerância.
        if abs(fx) < self.tolerancia:
            r.estado = ("Raiz fora do domínio físico"
                        if self.nao_negativo and x < 0 else "Convergiu")
            return True
        return False


def _extremidade_ja_e_raiz(registro, esquerda, f_esquerda, direita, f_direita):
    """Usado pelos métodos de intervalo: verifica as extremidades antes de exigir
    mudança de sinal. Uma aproximação inicial aceitável encerra com zero iterações."""
    if abs(f_esquerda) < registro.tolerancia:
        registro.registrar(esquerda, f_esquerda)
        return True
    if abs(f_direita) < registro.tolerancia:
        registro.registrar(direita, f_direita)
        return True
    return False


def _exigir_mudanca_de_sinal(f_esquerda, f_direita):
    # Comparar sinais diretamente evita overflow no produto f(a)*f(b).
    if (f_esquerda > 0) == (f_direita > 0):
        raise FalhaNumerica("Ausência de mudança de sinal no intervalo.")


# =============================================================================
# 3. Os quatro métodos
# =============================================================================

def bisseccao(f, registro, a, b, max_iteracoes):
    """Método da Bissecção (intervalo fechado).

    A cada iteração:
      1. calcula o ponto médio x = (esquerda + direita) / 2;
      2. avalia f(x) e testa o critério de parada;
      3. descarta a metade do intervalo que não contém mudança de sinal.
    """
    esquerda, direita = a, b
    f_esquerda, f_direita = valor_finito(f, esquerda), valor_finito(f, direita)
    if _extremidade_ja_e_raiz(registro, esquerda, f_esquerda, direita, f_direita):
        return
    _exigir_mudanca_de_sinal(f_esquerda, f_direita)

    anterior = None
    for iteracao in range(1, max_iteracoes + 1):
        registro.nova_iteracao(iteracao)

        # 1. Ponto médio: dividir antes de somar reduz o risco de overflow.
        x = esquerda / 2 + direita / 2

        # 2. Avaliação e critério de parada.
        fx = valor_finito(f, x)
        if registro.registrar(x, fx, anterior):
            return
        # Se o arredondamento impede novos avanços sem satisfazer o resíduo,
        # a execução estagnou e não deve ser declarada convergente.
        if x == anterior or x == esquerda or x == direita:
            raise FalhaNumerica("Estagnação sem atingir a tolerância residual.")

        # 3. Mantém o subintervalo cujas extremidades têm sinais opostos.
        if (f_esquerda > 0) != (fx > 0):
            direita, f_direita = x, fx
        else:
            esquerda, f_esquerda = x, fx
        anterior = x


def falsa_posicao(f, registro, a, b, max_iteracoes):
    """Método da Falsa Posição (intervalo fechado).

    A cada iteração:
      1. traça a reta entre (esquerda, f(esquerda)) e (direita, f(direita))
         e toma x como a interseção dessa reta com y = 0;
      2. avalia f(x) e testa o critério de parada;
      3. descarta o lado do intervalo que não contém mudança de sinal.
    """
    esquerda, direita = a, b
    f_esquerda, f_direita = valor_finito(f, esquerda), valor_finito(f, direita)
    if _extremidade_ja_e_raiz(registro, esquerda, f_esquerda, direita, f_direita):
        return
    _exigir_mudanca_de_sinal(f_esquerda, f_direita)

    anterior = None
    for iteracao in range(1, max_iteracoes + 1):
        registro.nova_iteracao(iteracao)

        # 1. Interseção da reta secante com o eixo x.
        # Magnitudes normalizadas evitam overflow na interpolação da Falsa Posição.
        # Para sinais opostos, peso = |f(a)| / (|f(a)| + |f(b)|).
        # A combinação abaixo é equivalente à interseção da reta com y=0.
        escala = max(abs(f_esquerda), abs(f_direita))
        peso = (abs(f_esquerda) / escala) / (abs(f_esquerda) / escala + abs(f_direita) / escala)
        x = (1 - peso) * esquerda + peso * direita

        # 2. Avaliação e critério de parada.
        fx = valor_finito(f, x)
        if registro.registrar(x, fx, anterior):
            return
        # Se o arredondamento impede novos avanços sem satisfazer o resíduo,
        # a execução estagnou e não deve ser declarada convergente.
        if x == anterior or x == esquerda or x == direita:
            raise FalhaNumerica("Estagnação sem atingir a tolerância residual.")

        # 3. Mantém o subintervalo cujas extremidades têm sinais opostos.
        if (f_esquerda > 0) != (fx > 0):
            direita, f_direita = x, fx
        else:
            esquerda, f_esquerda = x, fx
        anterior = x


def newton_raphson(f, derivada, registro, x0, max_iteracoes):
    """Método de Newton-Raphson (aberto, uma semente).

    A cada iteração:
      1. calcula a derivada f'(x) no ponto atual;
      2. toma o novo x como a interseção da reta tangente com y = 0:
         x_novo = x - f(x) / f'(x);
      3. avalia f(x_novo) e testa o critério de parada.
    """
    atual = x0
    f_atual = valor_finito(f, atual)
    if registro.registrar(atual, f_atual):
        return
    if derivada is None:
        raise FalhaNumerica("Informe a derivada para Newton-Raphson.")

    for iteracao in range(1, max_iteracoes + 1):
        registro.nova_iteracao(iteracao)

        # 1. Inclinação da tangente no ponto atual.
        inclinacao = valor_finito(derivada, atual)
        # Não se usa um limiar absoluto para derivada pequena: reescalar
        # f também reescala f', sem necessariamente prejudicar Newton.
        if inclinacao == 0:
            raise FalhaNumerica("Derivada nula: divisão por zero em Newton.")

        # 2. Interseção da tangente em x atual com o eixo horizontal.
        candidato = atual - f_atual / inclinacao

        # 3. Avaliação e critério de parada.
        valor = valor_finito(f, candidato)
        if registro.registrar(candidato, valor, atual):
            return
        if candidato == atual:
            raise FalhaNumerica("Estagnação sem atingir a tolerância residual.")

        atual, f_atual = candidato, valor


def secante(f, registro, x0, x1, max_iteracoes):
    """Método da Secante (aberto, duas sementes).

    A cada iteração:
      1. estima a inclinação pela reta que passa pelas duas últimas
         aproximações (substitui a derivada de Newton);
      2. toma o novo x como a interseção dessa reta com y = 0:
         x_novo = x - f(x) * (x - x_anterior) / (f(x) - f(x_anterior));
      3. avalia f(x_novo) e testa o critério de parada.
    """
    # As duas sementes pertencem à iteração zero do histórico.
    anterior = x0
    f_anterior = valor_finito(f, anterior)
    if registro.registrar(anterior, f_anterior):
        return
    atual = x1
    f_atual = valor_finito(f, atual)
    if registro.registrar(atual, f_atual, anterior):
        return

    for iteracao in range(1, max_iteracoes + 1):
        registro.nova_iteracao(iteracao)

        # 1. A Secante estima a inclinação usando as duas últimas amostras.
        denominador = f_atual - f_anterior
        if denominador == 0:
            raise FalhaNumerica("Valores de função iguais: divisão por zero na Secante.")

        # 2. Interseção da reta secante com o eixo horizontal.
        candidato = atual - (f_atual / denominador) * (atual - anterior)

        # 3. Avaliação e critério de parada.
        valor = valor_finito(f, candidato)
        if registro.registrar(candidato, valor, atual):
            return
        if candidato == atual:
            raise FalhaNumerica("Estagnação sem atingir a tolerância residual.")

        # Reaproveita a avaliação anterior; a Secante não recalcula f(x)
        # para as aproximações que já conhece.
        anterior, f_anterior = atual, f_atual
        atual, f_atual = candidato, valor


# =============================================================================
# 4. Ponto de entrada comum
# =============================================================================

NOMES = {"bisseccao": "Bissecção", "falsa_posicao": "Falsa Posição",
         "newton": "Newton-Raphson", "secante": "Secante"}


def resolver(metodo, f, *, a=0.0, b=1.0, x0=0.5, x1=1.0, derivada=None,
          tolerancia=1e-6, max_iteracoes=100, nao_negativo=False):
    """Mede o cálculo numérico e o histórico, excluindo interpretação e gráficos.

    Raízes iniciais contam como zero iterações. Cada atualização tentada conta uma.
    Métodos abertos podem sair de [a,b]; o evento é registrado, sem limitar o passo.
    """
    if metodo not in NOMES:
        raise ValueError("Método desconhecido.")
    # Configurações inválidas são rejeitadas antes de iniciar a cronometragem.
    if not math.isfinite(tolerancia) or tolerancia <= 0:
        raise ValueError("A tolerância deve ser positiva e finita.")
    if type(max_iteracoes) is not int or not 1 <= max_iteracoes <= 100000:
        raise ValueError("O limite deve ser um inteiro entre 1 e 100000.")
    if not all(math.isfinite(v) for v in (a, b, x0, x1)) or a >= b:
        raise ValueError("Use estimativas finitas e um intervalo com a < b.")

    resultado = Resultado(NOMES[metodo])
    registro = Registro(resultado, tolerancia=tolerancia, a=a, b=b,
                        nao_negativo=nao_negativo,
                        metodo_aberto=metodo in ("newton", "secante"))
    # O relógio mede somente a resolução, incluindo avaliações e histórico.
    inicio = perf_counter_ns()
    try:
        if metodo == "bisseccao":
            bisseccao(f, registro, a, b, max_iteracoes)
        elif metodo == "falsa_posicao":
            falsa_posicao(f, registro, a, b, max_iteracoes)
        elif metodo == "newton":
            newton_raphson(f, derivada, registro, x0, max_iteracoes)
        else:
            secante(f, registro, x0, x1, max_iteracoes)
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

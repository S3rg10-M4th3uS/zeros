"""Interpretador de expressões matemáticas restritas; não executa código Python."""
import ast
import math
import operator

# Lista explícita das funções aceitas: nomes fora dela não são executados.
FUNCOES = {nome: getattr(math, nome) for nome in (
    "sin", "cos", "tan", "exp", "log", "log10", "sqrt", "sinh", "cosh", "tanh", "asin", "acos", "atan"
)}
FUNCOES.update({"abs": abs, "sen": math.sin, "ln": math.log})
CONSTANTES = {"pi": math.pi, "e": math.e}
OPERADORES = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
             ast.Div: operator.truediv, ast.Pow: operator.pow}


def interpretar_expressao(fonte):
    """Aceita árvores aritméticas limitadas com uma variável real (x ou t)."""
    # Limites de tamanho e número de nós restringem o custo de interpretar a entrada.
    if not fonte.strip() or len(fonte) > 500:
        raise ValueError("A expressão deve conter entre 1 e 500 caracteres.")
    try:
        # A árvore descreve a expressão sem executá-la. O modo "eval" aceita
        # uma expressão, e a substituição permite escrever potências com ^.
        arvore = ast.parse(fonte.replace("^", "**"), mode="eval")
    except (SyntaxError, RecursionError) as erro:
        raise ValueError("Expressão inválida. Use, por exemplo, cos(x)-x.") from erro
    if sum(1 for _ in ast.walk(arvore)) > 150:
        raise ValueError("Expressão muito complexa.")

    # Visita cada parte da árvore e rejeita acessos a atributos, índices,
    # comandos e chamadas que não pertençam à linguagem matemática permitida.
    def validar(no):
        if isinstance(no, ast.Constant):
            # A comparação exata de tipos também exclui bool, que herda de int.
            if type(no.value) not in (int, float) or not math.isfinite(float(no.value)):
                raise ValueError("Use somente constantes reais finitas.")
        elif isinstance(no, ast.Name) and no.id in {"x", "t", *CONSTANTES}:
            pass
        elif isinstance(no, ast.BinOp) and type(no.op) in OPERADORES:
            validar(no.left)
            validar(no.right)
        elif isinstance(no, ast.UnaryOp) and isinstance(no.op, (ast.UAdd, ast.USub)):
            validar(no.operand)
        elif (isinstance(no, ast.Call) and isinstance(no.func, ast.Name)
              and no.func.id in FUNCOES and len(no.args) == 1 and not no.keywords):
            validar(no.args[0])
        else:
            raise ValueError("Operação não permitida. Use x ou t e funções matemáticas como sin, cos, exp e log.")

    # Só após validar a árvore inteira é criada a função usada pelos métodos.
    validar(arvore.body)

    # A avaliação é recursiva: resolve os operandos antes de aplicar a operação.
    # x e t representam o mesmo argumento; pi e e são constantes independentes.
    def avaliar(no, x):
        if isinstance(no, ast.Constant):
            return float(no.value)
        if isinstance(no, ast.Name):
            return x if no.id in ("x", "t") else CONSTANTES[no.id]
        if isinstance(no, ast.UnaryOp):
            valor = avaliar(no.operand, x)
            return -valor if isinstance(no.op, ast.USub) else valor
        if isinstance(no, ast.BinOp):
            # Ponto flutuante evita alocar inteiros enormes nas potências.
            return float(OPERADORES[type(no.op)](avaliar(no.left, x), avaliar(no.right, x)))
        return float(FUNCOES[no.func.id](avaliar(no.args[0], x)))

    # A árvore é reutilizada a cada chamada; não é necessário reler o texto
    # em cada iteração. Erros de domínio serão tratados em valor_finito.
    return lambda x: avaliar(arvore.body, float(x))

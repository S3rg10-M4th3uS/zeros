"""Exemplos do enunciado; x e t são intercambiáveis nas expressões."""
from math import log

# Os mesmos dados alimentam interface, testes e relatório. As referências
# permitem comparar o erro na raiz além do resíduo usado como critério de parada.
EXEMPLOS = {
    "Validação: cos(x) − x": dict(expressao="cos(x)-x", derivada="-sin(x)-1",
        a=0.0, b=1.0, x0=0.5, x1=1.0, secante_x0=0.0, referencia=0.7390851332151607,
        unidade="", nao_negativo=False),
    # T(t)=50 implica exp(-0.15t)=1/3, portanto t=ln(3)/0.15 minutos.
    "Resfriamento do componente": dict(expressao="90*exp(-0.15*t)-30", derivada="-13.5*exp(-0.15*t)",
        a=0.0, b=10.0, x0=0.0, x1=10.0, secante_x0=0.0, referencia=log(3)/0.15,
        unidade="min", nao_negativo=True),
    # V(t)=3.8 implica exp(-t)=0.24, portanto t=-ln(0.24) segundos.
    "Carregamento do capacitor": dict(expressao="5*(1-exp(-t))-3.8", derivada="5*exp(-t)",
        a=0.0, b=2.0, x0=0.0, x1=2.0, secante_x0=0.0, referencia=-log(0.24),
        unidade="s", nao_negativo=True),
}

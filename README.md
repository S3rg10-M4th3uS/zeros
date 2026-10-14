# Zeros · Cálculo Numérico


Simulador de Bissecção, Falsa Posição clássica, Newton-Raphson e Secante para o Projeto Unidade 1 (2026.2). Inclui os três exemplos do enunciado, funções personalizadas, tabela comparativa, gráficos, históricos e exportação CSV/JSON.

## Executar

Requer Python 3.13. Na pasta do projeto, crie um ambiente virtual:

```sh
python -m venv .venv
```

Ative no Linux/macOS:

```sh
source .venv/bin/activate
```

Ou no Windows (PowerShell):

```powershell
.venv\Scripts\Activate.ps1
```

Com o ambiente virtual ativo, instale as dependências e execute:

```sh
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Abra o endereço local mostrado no terminal (normalmente `http://localhost:8501`). Escolha um exemplo, ajuste os dados e clique em **Comparar métodos**. Para novos cálculos, altere os campos e clique novamente. Para sair, feche a aba e pressione `Ctrl+C` no terminal.

As versões das dependências diretas estão registradas em `requirements.txt`, com base no ambiente usado na validação do projeto.

## Entradas

- Função e derivada de Newton; variável `x` ou `t`.
- Intervalo `[a,b]`, estimativa de Newton e duas estimativas da Secante.
- Tolerância residual positiva e limite de iterações de 1 a 100000.
- Opção de exigir raiz não negativa para os problemas físicos.

Use ponto decimal, multiplicação explícita `*`, potências `^` ou `**`. Funções permitidas: `sin`/`sen`, `cos`, `tan`, `exp`, `log`/`ln`, `log10`, `sqrt`, `abs`, `sinh`, `cosh`, `tanh`, `asin`, `acos`, `atan`; constantes `pi`, `e`. Exemplos: `cos(x)-x`, `90*exp(-0.15*t)-30`. A entrada é interpretada por uma árvore restrita; não utiliza `eval`.

## Critérios e resultados

Sucesso significa **`abs(f(x)) < tolerância`**. O resíduo é apresentado como medida final exigida no enunciado; ele não é uma garantia do erro absoluto na raiz. O relatório também compara as raízes com referências independentes.

Raízes presentes nos dados iniciais contam como zero iterações. Cada tentativa de atualização conta uma iteração, incluindo tentativas que falham. As duas sementes da Secante aparecem na iteração zero. O tempo usa `perf_counter_ns`, inclui avaliações e histórico e exclui leitura da expressão, interface e gráficos. A interface mostra uma execução; o relatório mostra a mediana de 31 execuções após aquecimento.

Bissecção e Falsa Posição exigem função contínua e sinais opostos, salvo raiz nas extremidades. O programa verifica sinais, mas não prova continuidade. Newton e Secante podem sair do intervalo: isso gera aviso, sem alterar o método. Derivada nula, denominador nulo, domínio inválido, valores não finitos, estagnação e limite de iterações têm mensagens explícitas. Na falha, a tabela pode mostrar a última aproximação válida, sem rotulá-la como convergida. A derivada fornecida é responsabilidade do usuário.

## Exemplos

Todos usam tolerância `1e-6` e máximo de 100 iterações. Secante usa as extremidades do intervalo.

| Caso | Intervalo | Newton | Raiz de referência |
|---|---|---|---|
| `cos(x)-x` | `[0,1]` | `0.5` | `0.7390851332151607` |
| `90*exp(-0.15*t)-30` | `[0,10]` | `0` | `ln(3)/0.15` minutos |
| `5*(1-exp(-t))-3.8` | `[0,2]` | `0` | `-ln(0.24)` segundos |

## Validar e gerar o relatório

```sh
python -m unittest discover -s tests -v
python -m report.gerar
```

O gerador produz `report/relatorio.pdf`, uma versão Markdown, seis gráficos e resultados CSV/JSON. O JSON preserva entradas, históricos, ambiente e amostras temporais. Os tempos mudam entre execuções.

## Organização

- `src/metodos.py`: algoritmos e estados de execução.
- `src/expressoes.py`: interpretador matemático restrito.
- `src/comparacao.py`: comparação e tabela.
- `src/exemplos.py`: dados dos exemplos.
- `src/graficos.py`: gráficos da função e convergência.
- `app.py`: interface Streamlit.
- `tests/`: validação numérica e de entradas.
- `report/gerar.py`: geração do relatório a partir de novas medições.


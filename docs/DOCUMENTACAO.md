# Documentação Técnica — Analisador de Dados

Este documento descreve a arquitetura interna, os módulos e as decisões de projeto
da aplicação. Para instruções de instalação e uso rápido, veja o [README](../README.md).

## 1. Visão geral da arquitetura

O projeto é organizado em quatro etapas independentes — **fonte de dados**,
**motor de análise**, **gráficos** e **exportação** — conectadas por um único
contrato de dados (`RelatorioPlanilha`), o que permite combinar qualquer fonte
com qualquer motor e qualquer saída sem acoplamento entre eles.

```
Fonte de dados                Motor de análise         Gráficos + Exportação
──────────────                ────────────────         ──────────────────────
arquivo local  ─┐                                     ┌─ matplotlib → PDF
                 ├─► DataFrame ─► pandas ou polars ─► RelatorioPlanilha ─┤
Kaggle API      ─┤   (pandas/polars)                                    └─ plotly → HTML
Google BigQuery ─┘
```

`main.py` é o único ponto de entrada (CLI) e apenas orquestra essas etapas —
não contém lógica de negócio.

## 2. Módulos

### 2.1 Fontes de dados

#### `analisador/leitor.py` — `LeitorPlanilha`

Lê arquivos locais. Valida existência e formato do arquivo no construtor
(`FileNotFoundError` / `ValueError`).

- `carregar(planilha=0)` → `pandas.DataFrame`.
  - `.csv` → tenta os separadores `,`, `;`, `\t` e `|`, nessa ordem, e usa o
    primeiro que resultar em mais de uma coluna (heurística para lidar com
    planilhas exportadas em pt-BR, que costumam usar `;`).
  - `.tsv` → separador fixo `\t`.
  - `.xlsx` / `.xls` / `.xlsm` / `.ods` → `pandas.read_excel`.
- `carregar_polars(planilha=0)` → `polars.DataFrame`. CSV/TSV são lidos
  nativamente pelo Polars; Excel/ODS são carregados via pandas e convertidos
  com `pl.from_pandas`, evitando exigir engines extras do Polars (ex.
  `fastexcel`) só para esse caso.
- `listar_abas()` → nomes das abas de um arquivo Excel/ODS.

#### `analisador/fontes/kaggle_fonte.py` — `FonteKaggle`

Baixa um dataset do Kaggle (pacote oficial `kaggle`) e carrega um dos seus
CSVs em `pandas.DataFrame`.

```python
FonteKaggle().baixar_dataset("zynicide/wine-reviews")
```

Requer credenciais em `~/.kaggle/kaggle.json` (geradas em
kaggle.com/settings → API → Create New Token) ou nas variáveis de ambiente
`KAGGLE_USERNAME`/`KAGGLE_KEY` (ou `KAGGLE_API_TOKEN`).

> **Detalhe importante de implementação:** em versões recentes do pacote
> `kaggle` (≥ 2.x, baseado no `kagglesdk`), o simples `import kaggle` já
> executa a checagem de autenticação internamente e **encerra o processo
> inteiro** se não houver credenciais — sem levantar nenhuma exceção
> capturável em Python. Por isso `FonteKaggle` verifica a presença das
> credenciais (arquivos/variáveis de ambiente, via `_verificar_credenciais`)
> usando **apenas `importlib.util.find_spec`** (que localiza o módulo sem
> executá-lo) antes de fazer o `import` de fato. Isso garante que a ausência
> de credenciais vire um `RuntimeError` tratável pela CLI, em vez de matar o
> processo sem explicação.

#### `analisador/fontes/google_fonte.py` — `FonteGoogleBigQuery`

Executa uma consulta SQL no Google BigQuery e devolve o resultado em
`pandas.DataFrame`. Dá acesso a dezenas de datasets públicos do Google (ex.
`bigquery-public-data.covid19_open_data`, `bigquery-public-data.google_trends`).

```python
FonteGoogleBigQuery(projeto_gcp="meu-projeto").consultar(
    "SELECT * FROM `bigquery-public-data.covid19_open_data.covid19_open_data` LIMIT 1000"
)
```

Requer um projeto do Google Cloud com a API do BigQuery habilitada e
autenticação via `gcloud auth application-default login` ou uma service
account. Falhas de autenticação/criação do cliente são convertidas em
`RuntimeError` com instruções de como resolver.

### 2.2 Motor de análise

Ambos os motores produzem a mesma dataclass `RelatorioPlanilha`
(`analisador/relatorio.py`), o que torna gráficos e exportadores agnósticos
a qual motor gerou os dados:

| Campo                      | Origem                                                |
|-----------------------------|--------------------------------------------------------|
| `linhas` / `colunas`         | shape do DataFrame                                      |
| `colunas_numericas`          | colunas de tipo numérico                                 |
| `colunas_categoricas`        | demais colunas                                           |
| `valores_ausentes`           | contagem de nulos por coluna                             |
| `linhas_duplicadas`          | linhas duplicadas                                        |
| `estatisticas_numericas`     | describe (média, desvio, quartis) por coluna numérica     |
| `top_categorias`             | top 5 valores mais frequentes por coluna categórica        |
| `correlacoes`                | matriz de correlação (só quando há ≥ 2 colunas numéricas)  |

- **`analisador/relatorio.py` — `AnalisadorPlanilha`**: motor padrão, usa
  pandas (`describe()`, `value_counts()`, `corr()`).
- **`analisador/relatorio_polars.py` — `AnalisadorPolars`**: motor
  alternativo, com os cálculos pesados (`describe`, `group_by().len()`,
  `corr`) executados em Polars — mais rápido em datasets grandes por operar
  em paralelo com execução interna otimizada. O resultado final (tabelas
  pequenas de agregados) é convertido para pandas apenas na saída, para
  reaproveitar os mesmos módulos de gráfico/exportação do motor pandas.
  A correlação é calculada após `drop_nulls()` (exclusão listwise), uma
  aproximação razoável do comportamento pairwise do pandas.

### 2.3 Gráficos

Duas implementações paralelas, com a mesma interface de métodos
(`histogramas`, `graficos_categoricos`, `mapa_correlacao`,
`grafico_valores_ausentes`), cada uma devolvendo figuras no formato nativo
da sua biblioteca:

- **`analisador/graficos.py` — `GeradorGraficos`**: figuras `matplotlib`,
  usadas na exportação em PDF. Backend forçado para `Agg`
  (`matplotlib.use("Agg")`) por rodar em CLI, sem necessidade de janela
  interativa.
- **`analisador/graficos_plotly.py` — `GeradorGraficosPlotly`**: figuras
  `plotly.graph_objects.Figure` interativas (zoom, hover, pan), usadas na
  exportação em HTML.

### 2.4 Exportação

- **`analisador/exportador_pdf.py` — `ExportadorPDF`**: usa
  `matplotlib.backends.backend_pdf.PdfPages` para montar um único PDF
  multi-página (capa, resumo, tabela de estatísticas, gráficos), sem
  depender de bibliotecas adicionais de geração de PDF.
- **`analisador/exportador_html.py` — `ExportadorHTML`**: monta um único
  arquivo HTML autocontido (CSS inline, sem dependências externas), com
  resumo, tabela de estatísticas e os gráficos Plotly interativos embutidos.
  A biblioteca `plotly.js` é embutida (`include_plotlyjs="inline"`) apenas na
  primeira figura, para o arquivo final funcionar totalmente offline sem
  depender de CDN.

### 2.5 `main.py` — CLI

Construída com `argparse` e três subcomandos, cada um resolvendo a fonte de
dados e devolvendo `(dados, nome_para_relatorio)`:

```bash
python main.py arquivo <caminho> [--aba ABA]
python main.py kaggle <dataset> [--arquivo ARQUIVO]
python main.py bigquery "<query SQL>" [--projeto PROJETO]
```

Flags comuns aos três subcomandos:

- `--engine {pandas,polars}` (padrão `pandas`) — motor de análise.
- `--graficos {matplotlib,plotly}` (padrão `matplotlib`) — biblioteca de
  gráficos; `matplotlib` gera PDF, `plotly` gera HTML.
- `-o/--saida` — caminho do relatório de saída (padrão:
  `output/<nome>_relatorio.pdf` ou `.html`).

Fluxo: `_carregar_dados()` resolve a fonte → checagem de dados vazios →
`AnalisadorPlanilha` ou `AnalisadorPolars` gera o `RelatorioPlanilha` →
`ExportadorPDF` ou `ExportadorHTML` grava o arquivo final. Erros de leitura,
autenticação ou formato (`FileNotFoundError`, `ValueError`, `ImportError`,
`RuntimeError`) são capturados no nível da CLI e reportados via `stderr` com
código de saída `1`.

## 3. Decisões de projeto

- **`RelatorioPlanilha` como contrato único entre motor e apresentação**:
  pandas e Polars produzem exatamente a mesma estrutura de saída, então
  gráficos e exportadores não precisam saber qual motor rodou a análise.
- **DataFrame como contrato entre leitura e análise**: qualquer formato de
  arquivo que o pandas/Polars consigam ler alimenta o restante do pipeline
  sem alterações.
- **Só pandas + matplotlib para o PDF**: `PdfPages` do próprio matplotlib já
  produz PDFs vetoriais de boa qualidade com texto, tabelas e gráficos, sem
  exigir bibliotecas pesadas de geração de documento (reportlab, weasyprint).
- **HTML autocontido para o Plotly**: em vez de depender de um servidor local
  ou de CDN externo, o relatório HTML embute o `plotly.js` uma única vez,
  gerando um arquivo único que pode ser aberto offline e compartilhado por
  e-mail.
- **Checagem de credenciais antes do import problemático do Kaggle**: ver
  nota em [2.1](#analisadorfonteskaggle_fontepy--fontekaggle) — decisão
  motivada por um comportamento de hard-exit encontrado durante os testes,
  não documentado pela biblioteca.
- **Heurística de separador de CSV**: planilhas exportadas em português do
  Brasil frequentemente usam `;` como separador (porque `,` é o separador
  decimal); a detecção automática evita que o usuário precise saber disso.

## 4. Testes

Os testes ficam em [`testes/test_pipeline.py`](../testes/test_pipeline.py) e
cobrem:

- leitura de um CSV válido com pandas e com Polars;
- erro ao apontar para um arquivo inexistente ou formato não suportado;
- consistência entre `AnalisadorPlanilha` (pandas) e `AnalisadorPolars`
  (Polars) sobre o mesmo dataset — os dois devem produzir o mesmo número de
  linhas/colunas, mesmas colunas numéricas/categóricas e mesma contagem de
  valores ausentes;
- geração de um PDF não vazio e de um HTML com gráficos Plotly embutidos;
- que `FonteKaggle` e `FonteGoogleBigQuery` levantam um erro tratável (não um
  crash) quando não há credenciais configuradas no ambiente.

Para rodar:

```bash
pytest testes/
# ou, sem dependências extras:
python testes/test_pipeline.py
```

## 5. Extensão futura

- **Nova fonte de dados**: criar um módulo em `analisador/fontes/` que
  devolva um `pandas.DataFrame` (seguindo o padrão de `FonteKaggle`/
  `FonteGoogleBigQuery`) e um novo subcomando em `main.py`.
- **Novo motor de análise**: implementar uma classe com um método
  `gerar_relatorio() -> RelatorioPlanilha`, reaproveitando os mesmos
  gráficos/exportadores.
- **Novo formato de saída**: criar um `exportador_*.py` que receba o mesmo
  `RelatorioPlanilha` + DataFrame usado pelos exportadores existentes.
- **Interface gráfica ou web**: nenhum módulo em `analisador/` depende da
  CLI — podem ser reutilizados por uma UI (ex. Streamlit) chamando as mesmas
  classes.

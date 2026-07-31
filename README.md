# 📊 Analisador de Dados

Aplicação em Python que unifica leitura de planilhas locais e de APIs de
dados públicos (**Kaggle**, **Google BigQuery**), analisa com **pandas** ou
**Polars**, e entrega um relatório visual pronto para compartilhar — em
**PDF** (matplotlib) ou **HTML interativo** (Plotly) — em um único comando.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![pandas](https://img.shields.io/badge/pandas-2.x-150458?logo=pandas&logoColor=white)
![polars](https://img.shields.io/badge/polars-1.x-CD792C?logo=polars&logoColor=white)
![matplotlib](https://img.shields.io/badge/matplotlib-3.x-11557C?logo=plotly&logoColor=white)
![plotly](https://img.shields.io/badge/plotly-6.x-3F4F75?logo=plotly&logoColor=white)
![Licença](https://img.shields.io/badge/licença-MIT-green)

---

## ✨ Por que este projeto

Times de dados raramente trabalham só com arquivos locais: parte da análise
vem de datasets públicos (Kaggle, BigQuery), parte de exportações internas
(CSV/Excel). Este projeto unifica os dois mundos numa única interface de
linha de comando, com dois motores de análise (pandas para o dia a dia,
Polars para volumes maiores) e duas formas de entregar o resultado — PDF
estático para e-mail/impressão, ou HTML interativo para exploração.

## 🚀 Funcionalidades

- **Múltiplas fontes de dados**
  - Arquivos locais: `.csv`, `.tsv`, `.xlsx`, `.xls`, `.xlsm`, `.ods`, com
    detecção automática de separador e de aba.
  - **Kaggle** — baixa e analisa qualquer dataset público via API oficial.
  - **Google BigQuery** — consulta datasets públicos do Google (COVID-19,
    Google Trends, censo, clima, entre dezenas de outros) com SQL padrão.
- **Dois motores de análise, mesma saída** — `--engine pandas` (padrão) ou
  `--engine polars`, intercambiáveis sem mudar nada no restante do comando.
- **Relatório estatístico automático** — total de linhas/colunas, tipos de
  dado, valores ausentes, linhas duplicadas, estatísticas descritivas
  (média, mediana, desvio padrão, quartis), top valores por categoria e
  matriz de correlação.
- **Dois backends de gráficos** — `--graficos matplotlib` gera um PDF
  estático (histogramas, barras, heatmap de correlação); `--graficos plotly`
  gera um HTML interativo (zoom, hover, pan) autocontido, que abre offline
  em qualquer navegador.
- **100% linha de comando** — fácil de integrar em rotinas automatizadas ou
  pipelines de dados.

## 🖥️ Demonstração rápida

```bash
# Arquivo local, motor padrão (pandas), saída em PDF
python main.py arquivo exemplos/vendas_exemplo.csv
```

```
Dados carregados (pandas): 30 linhas, 8 colunas
Relatório gerado com sucesso em: output/vendas_exemplo_relatorio.pdf
```

```bash
# Mesmo arquivo, motor Polars e relatório interativo em HTML
python main.py arquivo exemplos/vendas_exemplo.csv --engine polars --graficos plotly
```

```bash
# Dataset público do Kaggle
python main.py kaggle zynicide/wine-reviews

# Dataset público do Google BigQuery
python main.py bigquery "SELECT * FROM \`bigquery-public-data.covid19_open_data.covid19_open_data\` LIMIT 1000" --projeto meu-projeto-gcp
```

O relatório (PDF ou HTML) contém, nessa ordem: resumo geral, tabela de
estatísticas, histogramas de cada coluna numérica, gráficos de barra das
colunas categóricas, mapa de correlação e gráfico de valores ausentes.

## 📦 Instalação

```bash
git clone <url-do-repositorio>
cd Analisador_Planilhas
pip install -r requirements.txt
```

Requer Python 3.10+. Para ler arquivos `.xls` antigos ou `.ods` localmente,
instale também `xlrd` e/ou `odfpy` (veja `requirements.txt`).

### Credenciais das APIs (opcional, só para `kaggle`/`bigquery`)

| Fonte      | Como configurar                                                                                       |
|-------------|----------------------------------------------------------------------------------------------------------|
| **Kaggle**   | Gere um token em kaggle.com → *Settings* → *API* → *Create New Token* e salve em `~/.kaggle/kaggle.json`, ou defina `KAGGLE_USERNAME`/`KAGGLE_KEY`. |
| **BigQuery** | Crie um projeto no Google Cloud com a API do BigQuery habilitada e rode `gcloud auth application-default login`. |

A leitura de arquivos locais (`arquivo`) não precisa de nenhuma credencial.

## ▶️ Uso

```bash
python main.py <fonte> [argumentos] [opções]
```

**Fontes disponíveis:**

| Subcomando   | Argumento                          | Descrição                                    |
|---------------|---------------------------------------|--------------------------------------------------|
| `arquivo`      | `caminho`                              | Analisa um arquivo local                          |
| `kaggle`       | `dataset` (ex.: `usuario/nome-dataset`)  | Baixa e analisa um dataset do Kaggle                |
| `bigquery`     | `query` (SQL)                           | Executa uma consulta em datasets públicos do BigQuery |

**Opções comuns a todas as fontes:**

| Opção            | Descrição                                                             | Padrão       |
|-------------------|---------------------------------------------------------------------------|----------------|
| `-o`, `--saida`    | Caminho do relatório de saída                                               | `output/<nome>_relatorio.{pdf,html}` |
| `--engine`         | Motor de análise: `pandas` ou `polars`                                       | `pandas`       |
| `--graficos`       | Biblioteca de gráficos: `matplotlib` (→ PDF) ou `plotly` (→ HTML)              | `matplotlib`   |

**Opções específicas:**

- `arquivo --aba` — índice ou nome da aba, para Excel/ODS com múltiplas abas.
- `kaggle --arquivo` — nome do CSV dentro do dataset (padrão: primeiro encontrado).
- `bigquery --projeto` — ID do projeto do Google Cloud a faturar pela consulta.

## 🏗️ Arquitetura

```
main.py                          → CLI (argparse, 3 subcomandos)
analisador/
  leitor.py                       → leitura local: CSV/Excel/ODS → pandas ou polars
  fontes/
    kaggle_fonte.py                 → download de datasets do Kaggle
    google_fonte.py                  → consultas ao Google BigQuery
  relatorio.py                       → motor de análise (pandas)
  relatorio_polars.py                 → motor de análise (Polars)
  graficos.py                          → gráficos matplotlib
  graficos_plotly.py                    → gráficos plotly
  exportador_pdf.py                      → relatório em PDF
  exportador_html.py                      → relatório em HTML interativo
exemplos/vendas_exemplo.csv          → dataset de demonstração
testes/test_pipeline.py               → testes automatizados
docs/DOCUMENTACAO.md                   → documentação técnica detalhada
```

Detalhes de design, decisões de arquitetura e pontos de extensão estão em
[docs/DOCUMENTACAO.md](docs/DOCUMENTACAO.md).

## 🛠️ Stack técnica

- **[pandas](https://pandas.pydata.org/)** / **[Polars](https://pola.rs/)** — leitura e análise dos dados.
- **[matplotlib](https://matplotlib.org/)** — gráficos e PDF (via `PdfPages`).
- **[Plotly](https://plotly.com/python/)** — gráficos interativos e relatório HTML.
- **[kaggle](https://github.com/Kaggle/kaggle-api)** — acesso a datasets do Kaggle.
- **[google-cloud-bigquery](https://cloud.google.com/python/docs/reference/bigquery/latest)** — acesso a datasets públicos do Google.
- **[openpyxl](https://openpyxl.readthedocs.io/)** — leitura de arquivos `.xlsx`/`.xlsm`.

## ✅ Testes

```bash
pytest testes/
# ou, sem dependências extras:
python testes/test_pipeline.py
```

Cobrem leitura (pandas e Polars), consistência entre os dois motores de
análise, geração de PDF e de HTML, e tratamento de erro das fontes Kaggle/
BigQuery quando não há credenciais configuradas.

## 📄 Licença

Distribuído sob a licença MIT. Sinta-se livre para usar este projeto como
base para seus próprios relatórios automatizados.

---

Desenvolvido como parte de um portfólio de projetos em Python voltados para
automação de análise de dados.

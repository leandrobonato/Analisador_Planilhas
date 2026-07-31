"""Analisador de Dados — ponto de entrada da aplicação (linha de comando).

Uso:
    python main.py arquivo dados.csv
    python main.py arquivo dados.xlsx --engine polars --graficos plotly
    python main.py kaggle zynicide/wine-reviews
    python main.py bigquery "SELECT * FROM \\`bigquery-public-data.covid19_open_data.covid19_open_data\\` LIMIT 1000" --projeto meu-projeto-gcp
"""

import argparse
import sys
from pathlib import Path

from analisador.exportador_html import ExportadorHTML
from analisador.exportador_pdf import ExportadorPDF
from analisador.fontes.google_fonte import FonteGoogleBigQuery
from analisador.fontes.kaggle_fonte import FonteKaggle
from analisador.leitor import LeitorPlanilha
from analisador.relatorio import AnalisadorPlanilha
from analisador.relatorio_polars import AnalisadorPolars


def criar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="analisador-dados",
        description=(
            "Lê dados de arquivos locais ou de APIs (Kaggle, Google BigQuery), "
            "analisa com pandas ou polars e gera um relatório com gráficos em "
            "PDF (matplotlib) ou HTML interativo (plotly)."
        ),
    )
    subparsers = parser.add_subparsers(dest="fonte", required=True)

    comum = argparse.ArgumentParser(add_help=False)
    comum.add_argument("-o", "--saida", default=None, help="Caminho do relatório de saída.")
    comum.add_argument(
        "--engine", choices=["pandas", "polars"], default="pandas",
        help="Motor de análise estatística (padrão: pandas).",
    )
    comum.add_argument(
        "--graficos", choices=["matplotlib", "plotly"], default="matplotlib",
        help=(
            "Biblioteca usada para os gráficos: 'matplotlib' gera um PDF, "
            "'plotly' gera um HTML interativo (padrão: matplotlib)."
        ),
    )

    p_arquivo = subparsers.add_parser(
        "arquivo", parents=[comum], help="Analisa um arquivo local (CSV/TSV/XLSX/XLS/ODS)."
    )
    p_arquivo.add_argument("caminho", help="Caminho do arquivo a ser analisado.")
    p_arquivo.add_argument(
        "--aba", default=0, help="Índice ou nome da aba, para arquivos Excel/ODS (padrão: 0)."
    )

    p_kaggle = subparsers.add_parser(
        "kaggle", parents=[comum], help="Baixa e analisa um dataset do Kaggle."
    )
    p_kaggle.add_argument("dataset", help="Identificador do dataset, ex.: usuario/nome-do-dataset.")
    p_kaggle.add_argument(
        "--arquivo", default=None, help="Nome do CSV dentro do dataset (padrão: primeiro encontrado)."
    )

    p_bigquery = subparsers.add_parser(
        "bigquery", parents=[comum], help="Executa uma consulta em datasets públicos do Google BigQuery."
    )
    p_bigquery.add_argument("query", help="Consulta SQL a ser executada no BigQuery.")
    p_bigquery.add_argument(
        "--projeto", default=None, help="ID do projeto do Google Cloud a faturar pela consulta."
    )

    return parser


def _resolver_aba(valor):
    try:
        return int(valor)
    except (TypeError, ValueError):
        return valor


def _carregar_dados(args):
    """Devolve (dados, nome_para_relatorio) a partir da fonte escolhida pelo usuário."""
    if args.fonte == "arquivo":
        caminho = Path(args.caminho)
        leitor = LeitorPlanilha(caminho)
        if args.engine == "polars":
            dados = leitor.carregar_polars(planilha=_resolver_aba(args.aba))
        else:
            dados = leitor.carregar(planilha=_resolver_aba(args.aba))
        return dados, caminho.name

    if args.fonte == "kaggle":
        df = FonteKaggle().baixar_dataset(args.dataset, arquivo=args.arquivo)
        return _adaptar_engine(df, args.engine), f"kaggle_{args.dataset}"

    if args.fonte == "bigquery":
        df = FonteGoogleBigQuery(projeto_gcp=args.projeto).consultar(args.query)
        return _adaptar_engine(df, args.engine), "bigquery_consulta"

    raise ValueError(f"Fonte desconhecida: {args.fonte}")


def _adaptar_engine(df_pandas, engine: str):
    if engine == "polars":
        import polars as pl
        return pl.from_pandas(df_pandas)
    return df_pandas


def main(argv: list[str] | None = None) -> int:
    parser = criar_parser()
    args = parser.parse_args(argv)

    try:
        dados, nome = _carregar_dados(args)
    except (FileNotFoundError, ValueError, ImportError, RuntimeError) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 1

    vazio = dados.is_empty() if args.engine == "polars" else dados.empty
    if vazio:
        print("Aviso: não há dados para analisar. Nenhum relatório será gerado.", file=sys.stderr)
        return 1

    linhas = dados.height if args.engine == "polars" else dados.shape[0]
    colunas = dados.width if args.engine == "polars" else dados.shape[1]
    print(f"Dados carregados ({args.engine}): {linhas} linhas, {colunas} colunas")

    if args.engine == "polars":
        relatorio = AnalisadorPolars(dados, nome_arquivo=nome).gerar_relatorio()
        df_para_graficos = dados.to_pandas()
    else:
        relatorio = AnalisadorPlanilha(dados, nome_arquivo=nome).gerar_relatorio()
        df_para_graficos = dados

    nome_base = Path(nome.replace(":", "_").replace("/", "_")).stem or "relatorio"

    if args.graficos == "plotly":
        caminho_saida = Path(args.saida) if args.saida else Path("output") / f"{nome_base}_relatorio.html"
        exportador = ExportadorHTML(relatorio, df_para_graficos, caminho_saida)
    else:
        caminho_saida = Path(args.saida) if args.saida else Path("output") / f"{nome_base}_relatorio.pdf"
        exportador = ExportadorPDF(relatorio, df_para_graficos, caminho_saida)

    caminho_final = exportador.exportar()
    print(f"Relatório gerado com sucesso em: {caminho_final.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

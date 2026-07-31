"""Testes do pipeline: leitura -> análise (pandas/polars) -> exportação (PDF/HTML)."""

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import polars as pl

from analisador.exportador_html import ExportadorHTML
from analisador.exportador_pdf import ExportadorPDF
from analisador.fontes.google_fonte import FonteGoogleBigQuery
from analisador.fontes.kaggle_fonte import FonteKaggle
from analisador.leitor import LeitorPlanilha
from analisador.relatorio import AnalisadorPlanilha
from analisador.relatorio_polars import AnalisadorPolars

CAMINHO_EXEMPLO = RAIZ / "exemplos" / "vendas_exemplo.csv"


# --- Leitura ---------------------------------------------------------------

def test_leitor_carrega_csv_pandas():
    df = LeitorPlanilha(CAMINHO_EXEMPLO).carregar()
    assert not df.empty
    assert "Produto" in df.columns
    assert "Valor_Total" in df.columns


def test_leitor_carrega_csv_polars():
    df = LeitorPlanilha(CAMINHO_EXEMPLO).carregar_polars()
    assert isinstance(df, pl.DataFrame)
    assert not df.is_empty()
    assert "Produto" in df.columns


def test_leitor_arquivo_inexistente():
    try:
        LeitorPlanilha(RAIZ / "exemplos" / "nao_existe.csv")
        assert False, "deveria ter levantado FileNotFoundError"
    except FileNotFoundError:
        pass


def test_leitor_formato_nao_suportado(tmp_path):
    arquivo = tmp_path / "dados.txt"
    arquivo.write_text("a,b\n1,2")
    try:
        LeitorPlanilha(arquivo)
        assert False, "deveria ter levantado ValueError"
    except ValueError:
        pass


# --- Análise -----------------------------------------------------------------

def test_analisador_pandas_gera_relatorio_consistente():
    df = LeitorPlanilha(CAMINHO_EXEMPLO).carregar()
    relatorio = AnalisadorPlanilha(df, nome_arquivo=CAMINHO_EXEMPLO.name).gerar_relatorio()

    assert relatorio.linhas == len(df)
    assert relatorio.colunas == df.shape[1]
    assert "Quantidade" in relatorio.colunas_numericas
    assert "Produto" in relatorio.colunas_categoricas
    assert relatorio.valores_ausentes["Quantidade"] > 0
    assert relatorio.correlacoes is not None


def test_analisador_polars_gera_relatorio_equivalente_ao_pandas():
    df_pandas = LeitorPlanilha(CAMINHO_EXEMPLO).carregar()
    df_polars = LeitorPlanilha(CAMINHO_EXEMPLO).carregar_polars()

    relatorio_pandas = AnalisadorPlanilha(df_pandas, nome_arquivo=CAMINHO_EXEMPLO.name).gerar_relatorio()
    relatorio_polars = AnalisadorPolars(df_polars, nome_arquivo=CAMINHO_EXEMPLO.name).gerar_relatorio()

    assert relatorio_polars.linhas == relatorio_pandas.linhas
    assert relatorio_polars.colunas == relatorio_pandas.colunas
    assert sorted(relatorio_polars.colunas_numericas) == sorted(relatorio_pandas.colunas_numericas)
    assert sorted(relatorio_polars.colunas_categoricas) == sorted(relatorio_pandas.colunas_categoricas)
    assert relatorio_polars.valores_ausentes == relatorio_pandas.valores_ausentes
    assert relatorio_polars.linhas_duplicadas == relatorio_pandas.linhas_duplicadas
    assert not relatorio_polars.estatisticas_numericas.empty
    assert relatorio_polars.correlacoes is not None


# --- Exportação ----------------------------------------------------------------

def test_exportador_pdf_gera_arquivo(tmp_path):
    df = LeitorPlanilha(CAMINHO_EXEMPLO).carregar()
    relatorio = AnalisadorPlanilha(df, nome_arquivo=CAMINHO_EXEMPLO.name).gerar_relatorio()

    caminho_saida = tmp_path / "relatorio_teste.pdf"
    resultado = ExportadorPDF(relatorio, df, caminho_saida).exportar()

    assert resultado.exists()
    assert resultado.stat().st_size > 0


def test_exportador_html_gera_arquivo_com_graficos(tmp_path):
    df = LeitorPlanilha(CAMINHO_EXEMPLO).carregar()
    relatorio = AnalisadorPlanilha(df, nome_arquivo=CAMINHO_EXEMPLO.name).gerar_relatorio()

    caminho_saida = tmp_path / "relatorio_teste.html"
    resultado = ExportadorHTML(relatorio, df, caminho_saida).exportar()

    conteudo = resultado.read_text(encoding="utf-8")
    assert resultado.exists()
    assert "Plotly.newPlot" in conteudo
    assert "Relatório de Análise de Dados" in conteudo


# --- Fontes externas (sem credenciais configuradas) -----------------------------

def test_fonte_kaggle_sem_credenciais_levanta_erro_tratavel():
    try:
        FonteKaggle._verificar_credenciais()
    except RuntimeError as erro:
        assert "kaggle.json" in str(erro) or "KAGGLE" in str(erro)
    else:
        # ambiente de quem roda o teste já tem credenciais configuradas — ok
        pass


def test_fonte_bigquery_sem_credenciais_levanta_erro_tratavel():
    try:
        FonteGoogleBigQuery().consultar("SELECT 1")
        # ambiente de quem roda o teste já tem credenciais/projeto configurados — ok
    except RuntimeError as erro:
        assert "BigQuery" in str(erro) or "autenticação" in str(erro)


if __name__ == "__main__":
    import tempfile

    testes_simples = [
        test_leitor_carrega_csv_pandas,
        test_leitor_carrega_csv_polars,
        test_leitor_arquivo_inexistente,
        test_analisador_pandas_gera_relatorio_consistente,
        test_analisador_polars_gera_relatorio_equivalente_ao_pandas,
        test_fonte_kaggle_sem_credenciais_levanta_erro_tratavel,
        test_fonte_bigquery_sem_credenciais_levanta_erro_tratavel,
    ]
    for teste in testes_simples:
        teste()

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        test_leitor_formato_nao_suportado(tmp_path)
        test_exportador_pdf_gera_arquivo(tmp_path)
        test_exportador_html_gera_arquivo_com_graficos(tmp_path)

    print("Todos os testes passaram.")

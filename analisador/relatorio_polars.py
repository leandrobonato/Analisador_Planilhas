"""Análise estatística automática usando Polars como motor de cálculo.

Equivalente a `analisador.relatorio.AnalisadorPlanilha`, mas com os cálculos
pesados (describe, contagens, correlação) executados em Polars — mais rápido
em datasets grandes por operar em paralelo e com execução lazy internamente.
O resultado final é convertido para as mesmas estruturas pandas usadas pelo
restante do pipeline, de forma que `RelatorioPlanilha` seja idêntico
independentemente do motor escolhido, e os módulos de gráficos/exportação não
precisem saber qual motor gerou o relatório.
"""

import polars as pl
import pandas as pd

from .relatorio import RelatorioPlanilha

COLUNAS_ESTATISTICAS = ["count", "mean", "std", "min", "25%", "50%", "75%", "max"]


class AnalisadorPolars:
    """Gera um RelatorioPlanilha a partir de um `polars.DataFrame`."""

    def __init__(self, df: pl.DataFrame, nome_arquivo: str):
        self.df = df
        self.nome_arquivo = nome_arquivo

    def gerar_relatorio(self) -> RelatorioPlanilha:
        df = self.df
        colunas_numericas = [
            nome for nome, tipo in zip(df.columns, df.dtypes) if tipo.is_numeric()
        ]
        colunas_categoricas = [c for c in df.columns if c not in colunas_numericas]

        contagem_nulos = df.null_count().row(0)
        valores_ausentes = dict(zip(df.columns, contagem_nulos))

        return RelatorioPlanilha(
            nome_arquivo=self.nome_arquivo,
            linhas=df.height,
            colunas=df.width,
            colunas_numericas=colunas_numericas,
            colunas_categoricas=colunas_categoricas,
            valores_ausentes=valores_ausentes,
            linhas_duplicadas=df.height - df.unique().height,
            estatisticas_numericas=self._estatisticas_numericas(df, colunas_numericas),
            top_categorias=self._top_categorias(df, colunas_categoricas),
            correlacoes=self._correlacoes(df, colunas_numericas),
        )

    @staticmethod
    def _estatisticas_numericas(df: pl.DataFrame, colunas: list[str]) -> pd.DataFrame:
        if not colunas:
            return pd.DataFrame()

        tabela = df.select(colunas).describe().to_pandas().set_index("statistic").T
        presentes = [c for c in COLUNAS_ESTATISTICAS if c in tabela.columns]
        return tabela[presentes].astype(float)

    @staticmethod
    def _top_categorias(df: pl.DataFrame, colunas: list[str]) -> dict[str, pd.Series]:
        resultado = {}
        for coluna in colunas:
            contagem = (
                df.select(coluna)
                .drop_nulls()
                .group_by(coluna)
                .len()
                .sort("len", descending=True)
                .head(5)
            )
            serie = contagem.to_pandas().set_index(coluna)["len"]
            serie.name = "count"
            resultado[coluna] = serie
        return resultado

    @staticmethod
    def _correlacoes(df: pl.DataFrame, colunas: list[str]) -> pd.DataFrame | None:
        if len(colunas) < 2:
            return None
        # descarta linhas com nulos para que a correlação seja calculável
        return df.select(colunas).drop_nulls().to_pandas().corr()

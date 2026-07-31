"""Análise estatística automática de um DataFrame."""

from dataclasses import dataclass

import pandas as pd


@dataclass
class RelatorioPlanilha:
    """Resultado consolidado da análise de uma planilha."""

    nome_arquivo: str
    linhas: int
    colunas: int
    colunas_numericas: list[str]
    colunas_categoricas: list[str]
    valores_ausentes: dict[str, int]
    linhas_duplicadas: int
    estatisticas_numericas: pd.DataFrame
    top_categorias: dict[str, pd.Series]
    correlacoes: pd.DataFrame | None


class AnalisadorPlanilha:
    """Gera um relatório estatístico a partir de um DataFrame já carregado."""

    def __init__(self, df: pd.DataFrame, nome_arquivo: str):
        self.df = df
        self.nome_arquivo = nome_arquivo

    def gerar_relatorio(self) -> RelatorioPlanilha:
        df = self.df
        colunas_numericas = df.select_dtypes(include="number").columns.tolist()
        colunas_categoricas = df.select_dtypes(exclude="number").columns.tolist()

        estatisticas = (
            df[colunas_numericas].describe().T if colunas_numericas else pd.DataFrame()
        )

        top_categorias = {
            coluna: df[coluna].value_counts().head(5) for coluna in colunas_categoricas
        }

        correlacoes = (
            df[colunas_numericas].corr() if len(colunas_numericas) >= 2 else None
        )

        return RelatorioPlanilha(
            nome_arquivo=self.nome_arquivo,
            linhas=len(df),
            colunas=df.shape[1],
            colunas_numericas=colunas_numericas,
            colunas_categoricas=colunas_categoricas,
            valores_ausentes=df.isna().sum().to_dict(),
            linhas_duplicadas=int(df.duplicated().sum()),
            estatisticas_numericas=estatisticas,
            top_categorias=top_categorias,
            correlacoes=correlacoes,
        )

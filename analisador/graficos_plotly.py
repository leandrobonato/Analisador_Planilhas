"""Geração de gráficos interativos com Plotly (alternativa ao matplotlib)."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

COR_PRIMARIA = "#2E86AB"
COR_ALERTA = "#C1121F"


class GeradorGraficosPlotly:
    """Cria figuras Plotly interativas a partir de um DataFrame (pandas)."""

    def __init__(self, df: pd.DataFrame):
        self.df = df

    def histogramas(self, colunas: list[str], limite: int = 6) -> list[go.Figure]:
        figuras = []
        for coluna in colunas[:limite]:
            dados = self.df[[coluna]].dropna()
            if dados.empty:
                continue
            fig = px.histogram(
                dados, x=coluna, nbins=20,
                title=f"Distribuição de {coluna}",
                color_discrete_sequence=[COR_PRIMARIA],
            )
            fig.update_layout(yaxis_title="Frequência", showlegend=False)
            figuras.append(fig)
        return figuras

    def graficos_categoricos(self, colunas: list[str], limite: int = 4) -> list[go.Figure]:
        figuras = []
        for coluna in colunas[:limite]:
            contagem = self.df[coluna].value_counts().head(10)
            if contagem.empty:
                continue
            fig = px.bar(
                x=contagem.index.astype(str), y=contagem.values,
                title=f"Valores mais frequentes em {coluna}",
                color_discrete_sequence=[COR_PRIMARIA],
            )
            fig.update_layout(xaxis_title=coluna, yaxis_title="Contagem", showlegend=False)
            figuras.append(fig)
        return figuras

    def mapa_correlacao(self, correlacoes: pd.DataFrame | None) -> go.Figure | None:
        if correlacoes is None or correlacoes.empty:
            return None
        fig = px.imshow(
            correlacoes, text_auto=".2f", color_continuous_scale="RdBu_r",
            zmin=-1, zmax=1, title="Mapa de Correlação entre Colunas Numéricas",
        )
        return fig

    def grafico_valores_ausentes(self, valores_ausentes: dict[str, int]) -> go.Figure | None:
        serie = pd.Series(valores_ausentes)
        serie = serie[serie > 0].sort_values(ascending=False)
        if serie.empty:
            return None
        fig = px.bar(
            x=serie.index.astype(str), y=serie.values,
            title="Valores Ausentes por Coluna",
            color_discrete_sequence=[COR_ALERTA],
        )
        fig.update_layout(xaxis_title="Coluna", yaxis_title="Quantidade de valores ausentes", showlegend=False)
        return fig

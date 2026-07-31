"""Geração dos gráficos usados no relatório (matplotlib)."""

import matplotlib

matplotlib.use("Agg")  # renderização sem interface gráfica, necessária para exportar em PDF

import matplotlib.pyplot as plt
import pandas as pd

COR_PRIMARIA = "#2E86AB"
COR_ALERTA = "#C1121F"


class GeradorGraficos:
    """Cria figuras matplotlib a partir de um DataFrame."""

    def __init__(self, df: pd.DataFrame):
        self.df = df

    def histogramas(self, colunas: list[str], limite: int = 6) -> list[plt.Figure]:
        figuras = []
        for coluna in colunas[:limite]:
            dados = self.df[coluna].dropna()
            if dados.empty:
                continue
            fig, ax = plt.subplots(figsize=(7, 4))
            dados.plot(kind="hist", bins=20, ax=ax, color=COR_PRIMARIA, edgecolor="white")
            ax.set_title(f"Distribuição de {coluna}")
            ax.set_xlabel(coluna)
            ax.set_ylabel("Frequência")
            fig.tight_layout()
            figuras.append(fig)
        return figuras

    def graficos_categoricos(self, colunas: list[str], limite: int = 4) -> list[plt.Figure]:
        figuras = []
        for coluna in colunas[:limite]:
            contagem = self.df[coluna].value_counts().head(10)
            if contagem.empty:
                continue
            fig, ax = plt.subplots(figsize=(7, 4))
            contagem.plot(kind="bar", ax=ax, color=COR_PRIMARIA)
            ax.set_title(f"Valores mais frequentes em {coluna}")
            ax.set_ylabel("Contagem")
            plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
            fig.tight_layout()
            figuras.append(fig)
        return figuras

    def mapa_correlacao(self, correlacoes: pd.DataFrame | None) -> plt.Figure | None:
        if correlacoes is None or correlacoes.empty:
            return None
        fig, ax = plt.subplots(figsize=(7, 6))
        imagem = ax.imshow(correlacoes, cmap="coolwarm", vmin=-1, vmax=1)
        rotulos = correlacoes.columns
        ax.set_xticks(range(len(rotulos)))
        ax.set_yticks(range(len(rotulos)))
        ax.set_xticklabels(rotulos, rotation=45, ha="right")
        ax.set_yticklabels(rotulos)
        for i in range(len(rotulos)):
            for j in range(len(rotulos)):
                ax.text(
                    j, i, f"{correlacoes.iloc[i, j]:.2f}",
                    ha="center", va="center", fontsize=8,
                )
        fig.colorbar(imagem, ax=ax, label="Coeficiente de correlação")
        ax.set_title("Mapa de Correlação entre Colunas Numéricas")
        fig.tight_layout()
        return fig

    def grafico_valores_ausentes(self, valores_ausentes: dict[str, int]) -> plt.Figure | None:
        serie = pd.Series(valores_ausentes)
        serie = serie[serie > 0].sort_values(ascending=False)
        if serie.empty:
            return None
        fig, ax = plt.subplots(figsize=(7, 4))
        serie.plot(kind="bar", ax=ax, color=COR_ALERTA)
        ax.set_title("Valores Ausentes por Coluna")
        ax.set_ylabel("Quantidade de valores ausentes")
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
        fig.tight_layout()
        return fig

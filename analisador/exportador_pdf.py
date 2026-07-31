"""Exportação do relatório completo (resumo + estatísticas + gráficos) em PDF."""

from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages

from .graficos import GeradorGraficos
from .relatorio import RelatorioPlanilha

TAMANHO_RETRATO = (8.27, 11.69)  # folha A4 em polegadas
TAMANHO_PAISAGEM = (11.69, 8.27)


class ExportadorPDF:
    """Monta um PDF multi-página a partir de um RelatorioPlanilha."""

    def __init__(self, relatorio: RelatorioPlanilha, df: pd.DataFrame, caminho_saida: str | Path):
        self.relatorio = relatorio
        self.df = df
        self.caminho_saida = Path(caminho_saida)
        self.graficos = GeradorGraficos(df)

    def exportar(self) -> Path:
        self.caminho_saida.parent.mkdir(parents=True, exist_ok=True)

        with PdfPages(self.caminho_saida) as pdf:
            self._adicionar(pdf, self._pagina_capa())
            self._adicionar(pdf, self._pagina_resumo())

            if not self.relatorio.estatisticas_numericas.empty:
                self._adicionar(pdf, self._pagina_tabela_estatisticas())

            for figura in self.graficos.histogramas(self.relatorio.colunas_numericas):
                self._adicionar(pdf, figura)

            for figura in self.graficos.graficos_categoricos(self.relatorio.colunas_categoricas):
                self._adicionar(pdf, figura)

            figura_correlacao = self.graficos.mapa_correlacao(self.relatorio.correlacoes)
            if figura_correlacao:
                self._adicionar(pdf, figura_correlacao)

            figura_ausentes = self.graficos.grafico_valores_ausentes(self.relatorio.valores_ausentes)
            if figura_ausentes:
                self._adicionar(pdf, figura_ausentes)

            info = pdf.infodict()
            info["Title"] = f"Relatório - {self.relatorio.nome_arquivo}"
            info["Author"] = "Analisador de Planilhas"
            info["CreationDate"] = datetime.now()

        return self.caminho_saida

    @staticmethod
    def _adicionar(pdf: PdfPages, figura: plt.Figure) -> None:
        pdf.savefig(figura)
        plt.close(figura)

    def _pagina_capa(self) -> plt.Figure:
        fig = plt.figure(figsize=TAMANHO_RETRATO)
        fig.text(0.5, 0.65, "Relatório de Análise de Planilha", ha="center", fontsize=22, weight="bold")
        fig.text(0.5, 0.58, self.relatorio.nome_arquivo, ha="center", fontsize=14, color="#444444")
        fig.text(0.5, 0.50, f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}", ha="center", fontsize=11)
        fig.text(
            0.5, 0.40,
            f"{self.relatorio.linhas} linhas   •   {self.relatorio.colunas} colunas",
            ha="center", fontsize=11,
        )
        return fig

    def _pagina_resumo(self) -> plt.Figure:
        r = self.relatorio
        fig, ax = plt.subplots(figsize=TAMANHO_RETRATO)
        ax.axis("off")

        linhas_texto = [
            f"Linhas: {r.linhas}",
            f"Colunas: {r.colunas}",
            f"Colunas numéricas: {len(r.colunas_numericas)}",
            f"Colunas categóricas: {len(r.colunas_categoricas)}",
            f"Linhas duplicadas: {r.linhas_duplicadas}",
            f"Total de valores ausentes: {sum(r.valores_ausentes.values())}",
            "",
            "Colunas numéricas:",
            "  " + (", ".join(r.colunas_numericas) or "nenhuma"),
            "",
            "Colunas categóricas:",
            "  " + (", ".join(r.colunas_categoricas) or "nenhuma"),
        ]

        ax.text(0.05, 0.95, "Resumo Geral", fontsize=18, weight="bold", va="top", transform=ax.transAxes)
        ax.text(0.05, 0.88, "\n".join(linhas_texto), fontsize=11, va="top", transform=ax.transAxes)
        return fig

    def _pagina_tabela_estatisticas(self) -> plt.Figure:
        estatisticas = self.relatorio.estatisticas_numericas.round(2)
        fig, ax = plt.subplots(figsize=TAMANHO_PAISAGEM)
        ax.axis("off")
        ax.set_title("Estatísticas Descritivas", fontsize=16, weight="bold", pad=20)

        tabela = ax.table(
            cellText=estatisticas.values,
            rowLabels=estatisticas.index,
            colLabels=estatisticas.columns,
            loc="center",
            cellLoc="center",
        )
        tabela.auto_set_font_size(False)
        tabela.set_fontsize(8)
        tabela.scale(1, 1.5)
        return fig

"""Exportação do relatório completo (resumo + estatísticas + gráficos) em HTML interativo."""

from datetime import datetime
from pathlib import Path

import pandas as pd

from .graficos_plotly import GeradorGraficosPlotly
from .relatorio import RelatorioPlanilha

MODELO_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>{titulo}</title>
<style>
  :root {{ color-scheme: light; }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; padding: 2.5rem 1.5rem 4rem;
    font-family: -apple-system, "Segoe UI", Roboto, Arial, sans-serif;
    background: #f4f6f8; color: #1c2530;
  }}
  .container {{ max-width: 1000px; margin: 0 auto; }}
  header {{ margin-bottom: 2rem; }}
  h1 {{ font-size: 1.75rem; margin: 0 0 0.25rem; }}
  .subtitulo {{ color: #5b6b7c; font-size: 0.95rem; }}
  section {{
    background: #ffffff; border: 1px solid #e2e8ef; border-radius: 10px;
    padding: 1.5rem; margin-bottom: 1.5rem;
  }}
  section h2 {{ margin-top: 0; font-size: 1.15rem; color: #2E86AB; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 0.9rem; }}
  table th, table td {{ padding: 0.45rem 0.7rem; border-bottom: 1px solid #edf1f5; text-align: left; }}
  table.resumo th {{ width: 40%; color: #5b6b7c; font-weight: 500; }}
  table.estatisticas th {{ background: #f4f6f8; }}
  .grafico {{ margin-bottom: 1.5rem; }}
  footer {{ text-align: center; color: #8a97a6; font-size: 0.8rem; margin-top: 2rem; }}
</style>
</head>
<body>
  <div class="container">
    <header>
      <h1>Relatório de Análise de Dados</h1>
      <div class="subtitulo">{nome_arquivo} &middot; gerado em {data_geracao}</div>
    </header>

    <section>
      <h2>Resumo Geral</h2>
      {resumo_html}
    </section>

    <section>
      <h2>Estatísticas Descritivas</h2>
      {estatisticas_html}
    </section>

    <section>
      <h2>Gráficos</h2>
      {graficos_html}
    </section>

    <footer>Gerado automaticamente pelo Analisador de Dados.</footer>
  </div>
</body>
</html>
"""


class ExportadorHTML:
    """Monta um relatório HTML interativo e autocontido a partir de um RelatorioPlanilha."""

    def __init__(self, relatorio: RelatorioPlanilha, df: pd.DataFrame, caminho_saida: str | Path):
        self.relatorio = relatorio
        self.df = df
        self.caminho_saida = Path(caminho_saida)
        self.graficos = GeradorGraficosPlotly(df)

    def exportar(self) -> Path:
        self.caminho_saida.parent.mkdir(parents=True, exist_ok=True)

        figuras = [
            *self.graficos.histogramas(self.relatorio.colunas_numericas),
            *self.graficos.graficos_categoricos(self.relatorio.colunas_categoricas),
        ]
        figura_correlacao = self.graficos.mapa_correlacao(self.relatorio.correlacoes)
        if figura_correlacao:
            figuras.append(figura_correlacao)
        figura_ausentes = self.graficos.grafico_valores_ausentes(self.relatorio.valores_ausentes)
        if figura_ausentes:
            figuras.append(figura_ausentes)

        html = MODELO_HTML.format(
            titulo=f"Relatório - {self.relatorio.nome_arquivo}",
            nome_arquivo=self.relatorio.nome_arquivo,
            data_geracao=datetime.now().strftime("%d/%m/%Y %H:%M"),
            resumo_html=self._resumo_html(),
            estatisticas_html=self._tabela_estatisticas_html(),
            graficos_html=self._graficos_html(figuras),
        )

        self.caminho_saida.write_text(html, encoding="utf-8")
        return self.caminho_saida

    def _resumo_html(self) -> str:
        r = self.relatorio
        itens = [
            ("Linhas", r.linhas),
            ("Colunas", r.colunas),
            ("Colunas numéricas", len(r.colunas_numericas)),
            ("Colunas categóricas", len(r.colunas_categoricas)),
            ("Linhas duplicadas", r.linhas_duplicadas),
            ("Total de valores ausentes", sum(r.valores_ausentes.values())),
        ]
        linhas = "".join(f"<tr><th>{nome}</th><td>{valor}</td></tr>" for nome, valor in itens)
        return f"<table class='resumo'>{linhas}</table>"

    def _tabela_estatisticas_html(self) -> str:
        if self.relatorio.estatisticas_numericas.empty:
            return "<p>Nenhuma coluna numérica encontrada.</p>"
        return self.relatorio.estatisticas_numericas.round(2).to_html(classes="estatisticas", border=0)

    @staticmethod
    def _graficos_html(figuras: list) -> str:
        if not figuras:
            return "<p>Nenhum gráfico gerado.</p>"

        partes = []
        for indice, fig in enumerate(figuras):
            # inclui a biblioteca plotly.js embutida apenas na primeira figura,
            # para o HTML final funcionar offline sem depender de CDN externo
            incluir_plotlyjs = "inline" if indice == 0 else False
            partes.append(
                f'<div class="grafico">{fig.to_html(full_html=False, include_plotlyjs=incluir_plotlyjs, config={"responsive": True})}</div>'
            )
        return "\n".join(partes)

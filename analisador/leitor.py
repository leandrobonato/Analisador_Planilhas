"""Leitura de planilhas em múltiplos formatos (CSV, TSV, XLSX, XLS, ODS)."""

from pathlib import Path

import pandas as pd

FORMATOS_SUPORTADOS = {".csv", ".tsv", ".xlsx", ".xls", ".xlsm", ".ods"}
FORMATOS_EXCEL = {".xlsx", ".xls", ".xlsm", ".ods"}
SEPARADORES_CSV = (",", ";", "\t", "|")


class LeitorPlanilha:
    """Carrega uma planilha do disco para um DataFrame do pandas.

    Detecta o formato pela extensão do arquivo e, no caso de CSV/TSV,
    tenta identificar automaticamente o separador de colunas.
    """

    def __init__(self, caminho: str | Path):
        self.caminho = Path(caminho)
        if not self.caminho.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {self.caminho}")

        self.extensao = self.caminho.suffix.lower()
        if self.extensao not in FORMATOS_SUPORTADOS:
            formatos = ", ".join(sorted(FORMATOS_SUPORTADOS))
            raise ValueError(
                f"Formato '{self.extensao}' não suportado. Formatos aceitos: {formatos}"
            )

    def carregar(self, planilha: int | str = 0) -> pd.DataFrame:
        """Retorna o conteúdo do arquivo como DataFrame.

        Args:
            planilha: índice ou nome da aba, usado apenas para arquivos Excel/ODS.
        """
        if self.extensao == ".csv":
            return self._carregar_csv()
        if self.extensao == ".tsv":
            return pd.read_csv(self.caminho, sep="\t")
        return pd.read_excel(self.caminho, sheet_name=planilha)

    def carregar_polars(self, planilha: int | str = 0) -> "pl.DataFrame":
        """Retorna o conteúdo do arquivo como `polars.DataFrame`.

        CSV/TSV são lidos nativamente pelo Polars (mais rápido). Excel/ODS são
        carregados via pandas e convertidos, para não exigir engines extras
        do Polars (ex. `fastexcel`) apenas para esse caso.
        """
        import polars as pl

        if self.extensao == ".csv":
            for separador in SEPARADORES_CSV:
                try:
                    df = pl.read_csv(self.caminho, separator=separador)
                except Exception:
                    continue
                if df.width > 1:
                    return df
            return pl.read_csv(self.caminho)
        if self.extensao == ".tsv":
            return pl.read_csv(self.caminho, separator="\t")
        return pl.from_pandas(self.carregar(planilha=planilha))

    def listar_abas(self) -> list[str] | None:
        """Lista os nomes das abas disponíveis (apenas para Excel/ODS)."""
        if self.extensao not in FORMATOS_EXCEL:
            return None
        return pd.ExcelFile(self.caminho).sheet_names

    def _carregar_csv(self) -> pd.DataFrame:
        # Tenta separadores comuns até encontrar um que produza mais de uma coluna.
        for separador in SEPARADORES_CSV:
            try:
                df = pd.read_csv(self.caminho, sep=separador, engine="python")
            except Exception:
                continue
            if df.shape[1] > 1:
                return df
        return pd.read_csv(self.caminho)

"""Acesso a dados públicos do Google via BigQuery (pacote `google-cloud-bigquery`).

O BigQuery hospeda dezenas de datasets públicos prontos para consulta (ex.:
`bigquery-public-data.covid19_open_data`, `bigquery-public-data.google_trends`).
Requer um projeto do Google Cloud com a API do BigQuery habilitada e
autenticação via `gcloud auth application-default login` ou uma service
account (ver https://cloud.google.com/bigquery/docs/authentication). O nível
gratuito ("sandbox") do BigQuery permite consultar datasets públicos sem
custo, respeitando a cota gratuita mensal.
"""

import pandas as pd


class FonteGoogleBigQuery:
    """Executa consultas SQL no BigQuery e devolve o resultado em DataFrame."""

    def __init__(self, projeto_gcp: str | None = None):
        self.projeto_gcp = projeto_gcp

    def consultar(self, query: str) -> pd.DataFrame:
        """Executa `query` (SQL padrão do BigQuery) e devolve um DataFrame.

        Exemplo de query sobre um dataset público:
            SELECT * FROM `bigquery-public-data.covid19_open_data.covid19_open_data`
            LIMIT 1000
        """
        cliente = self._criar_cliente()
        try:
            return cliente.query(query).to_dataframe()
        except Exception as erro:
            raise RuntimeError(f"Falha ao executar a consulta no BigQuery: {erro}") from erro

    def _criar_cliente(self):
        try:
            from google.cloud import bigquery
        except ImportError as erro:
            raise ImportError(
                "A biblioteca 'google-cloud-bigquery' não está instalada. "
                "Rode: pip install google-cloud-bigquery"
            ) from erro

        try:
            return bigquery.Client(project=self.projeto_gcp)
        except Exception as erro:
            raise RuntimeError(
                "Não foi possível criar o cliente do BigQuery. Configure a "
                "autenticação com 'gcloud auth application-default login' ou "
                "defina a variável de ambiente GOOGLE_APPLICATION_CREDENTIALS "
                "apontando para uma chave de service account, e informe um "
                "projeto do Google Cloud com a API do BigQuery habilitada."
            ) from erro

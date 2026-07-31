"""Acesso a datasets do Kaggle via API oficial (pacote `kaggle`).

Requer credenciais configuradas em `~/.kaggle/kaggle.json`, geradas em
https://www.kaggle.com/settings -> API -> Create New Token.
"""

import importlib.util
from pathlib import Path

import pandas as pd

DIRETORIO_CACHE_PADRAO = Path("cache_kaggle")


class FonteKaggle:
    """Baixa um dataset do Kaggle e carrega um dos seus arquivos em DataFrame."""

    def __init__(self, diretorio_cache: str | Path = DIRETORIO_CACHE_PADRAO):
        self.diretorio_cache = Path(diretorio_cache)

    def baixar_dataset(self, dataset: str, arquivo: str | None = None) -> pd.DataFrame:
        """Baixa `dataset` (formato "usuario/nome-do-dataset") e devolve um DataFrame.

        Args:
            dataset: identificador do dataset no Kaggle, ex. "zynicide/wine-reviews".
            arquivo: nome do arquivo CSV a carregar dentro do dataset. Se omitido,
                usa o primeiro CSV encontrado após a extração.
        """
        api = self._autenticar()

        destino = self.diretorio_cache / dataset.replace("/", "__")
        destino.mkdir(parents=True, exist_ok=True)
        api.dataset_download_files(dataset, path=str(destino), unzip=True)

        caminho_csv = self._localizar_csv(destino, arquivo)
        return pd.read_csv(caminho_csv)

    def _autenticar(self):
        # Em versões recentes do pacote 'kaggle', o simples `import kaggle`
        # (mesmo o pacote vazio) já dispara a checagem de autenticação e
        # encerra o processo inteiro se não houver credenciais — sem levantar
        # nenhuma exceção capturável. Por isso a instalação é checada com
        # `find_spec` (não executa o módulo) e as credenciais são validadas
        # via arquivos/variáveis de ambiente ANTES de importar o pacote de fato.
        if importlib.util.find_spec("kaggle") is None:
            raise ImportError(
                "A biblioteca 'kaggle' não está instalada. Rode: pip install kaggle"
            )

        self._verificar_credenciais()

        from kaggle.api.kaggle_api_extended import KaggleApi

        api = KaggleApi()
        api.authenticate()
        return api

    @staticmethod
    def _verificar_credenciais() -> None:
        import os

        diretorio_config = Path(os.environ.get("KAGGLE_CONFIG_DIR", Path.home() / ".kaggle"))

        tem_credenciais = any([
            os.environ.get("KAGGLE_USERNAME") and os.environ.get("KAGGLE_KEY"),
            os.environ.get("KAGGLE_API_TOKEN"),
            (diretorio_config / "kaggle.json").exists(),
            (diretorio_config / "access_token").exists(),
        ])

        if not tem_credenciais:
            raise RuntimeError(
                "Credenciais do Kaggle não encontradas. Gere um token em "
                "https://www.kaggle.com/settings -> API -> Create New Token e salve "
                f"o arquivo baixado em {diretorio_config / 'kaggle.json'}, ou defina "
                "as variáveis de ambiente KAGGLE_USERNAME e KAGGLE_KEY "
                "(ou KAGGLE_API_TOKEN)."
            )

    @staticmethod
    def _localizar_csv(destino: Path, arquivo: str | None) -> Path:
        if arquivo:
            caminho = destino / arquivo
            if not caminho.exists():
                raise FileNotFoundError(f"Arquivo '{arquivo}' não encontrado em {destino}")
            return caminho

        candidatos = sorted(destino.glob("*.csv"))
        if not candidatos:
            raise FileNotFoundError(
                f"Nenhum arquivo .csv encontrado no dataset baixado em {destino}. "
                "Informe o parâmetro 'arquivo' com o nome exato."
            )
        return candidatos[0]

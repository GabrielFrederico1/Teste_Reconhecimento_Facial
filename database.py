"""
database.py

Protótipo de "banco de usuários" local em JSON.
No sistema final, isso seria substituído por uma tabela no backend (o app registra
lá, e o Pi consulta via API); para o protótipo da disciplina, um JSON local já
demonstra o conceito de matching sem depender de infraestrutura de servidor.
"""

import json
import os
import numpy as np

import config
from embedding import similaridade_cosseno


class BancoUsuarios:
    def __init__(self, caminho: str = config.DB_PATH):
        self.caminho = caminho
        self._dados = self._carregar()

    def _carregar(self) -> dict:
        if os.path.exists(self.caminho):
            with open(self.caminho, "r") as f:
                return json.load(f)
        return {}

    def salvar(self):
        with open(self.caminho, "w") as f:
            json.dump(self._dados, f, indent=2)

    def cadastrar(self, nome_usuario: str, embedding: np.ndarray):
        self._dados[nome_usuario] = embedding.tolist()
        self.salvar()

    def remover(self, nome_usuario: str):
        if nome_usuario in self._dados:
            del self._dados[nome_usuario]
            self.salvar()

    def buscar_mais_proximo(self, embedding: np.ndarray):
        """
        Retorna (nome_usuario, similaridade) do usuário mais parecido, ou (None, 0.0)
        se o banco estiver vazio.
        """
        melhor_nome, melhor_sim = None, -1.0
        for nome, vetor_salvo in self._dados.items():
            sim = similaridade_cosseno(embedding, np.array(vetor_salvo))
            if sim > melhor_sim:
                melhor_sim, melhor_nome = sim, nome
        return melhor_nome, max(melhor_sim, 0.0)

    def usuarios_cadastrados(self):
        return list(self._dados.keys())

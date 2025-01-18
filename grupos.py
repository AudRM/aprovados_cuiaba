"""

Classe para abstrair conjunto de atividades de grupos

"""
import pandas as pd 
from datetime import datetime 
from database import Database, TabelaAprovados, TabelaUsuario, TabelaGrupos

class Grupo:

    def __init__(self, grupo: str, db: Database) -> None:
        self.grupo = grupo 
        self.db = db 

    def mostrarEstatisticas(self) -> dict:
        dados = pd.DataFrame()

        return {
                'função': 'mostrarEstatisticas', 
                'data': datetime.now(), 
                'sucesso': True, 
                'resultado': dados
                }
    

    def verQuantidade(self) -> dict:
        
        usuarios = self.db.retornarTabela(TabelaUsuario)
        qtde_usuarios = len(usuarios[usuarios['grupo']==self.grupo])
        return {
                'função': 'verQuantidade', 
                'data': datetime.now(), 
                'sucesso': True, 
                'resultado': qtde_usuarios
                }



    def mostrarMensagens(self) -> dict:
        msg = None
        return {
                'função': 'mostrarMensagens', 
                'data': datetime.now(), 
                'sucesso': True, 
                'resultado': msg
                }
    

    def mostrarLink(self) -> dict:

        link = self.db.retornarValor(TabelaGrupos, filter_dict={'grupo': self.grupo})[0]['link']
        return {
                'função': 'mostrarLink', 
                'data': datetime.now(), 
                'sucesso': True, 
                'resultado': link
                }


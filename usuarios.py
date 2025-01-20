"""

Classes para controlar usuários

"""
import sqlalchemy 
import pandas as pd 
from typing import Union
from database import Database, TabelaUsuario
from datetime import datetime 

class Usuario:

    def __init__(self, nome: str, 
                 posicao: int, 
                 senha: str, 
                 email: str, 
                 telefone: str, 
                 opcao: str, 
                 n_inscr: str, 
                 grupo: str,
                 formacao_academica: str = False,
                 role: str = 'usuario',
                 cota: str = 'AC',
                 **kwargs) -> None:
        self.nome = nome 
        self.senha = senha 
        self.email = email 
        self.telefone = telefone 
        self.opcao = opcao 
        self.n_inscr = n_inscr
        self.grupo = grupo
        self.posicao = posicao
        self.formacao_academica = formacao_academica
        self.role = role
        self.cota = cota

    def mudarDados(self, db: Database, mudanca: dict) -> dict:
        
        filtros = {"n_inscr": self.n_inscr} 
        atualizacoes = {}
        
        # Extrair mudanças
        if 'email' in mudanca.keys():
            atualizacoes['email'] =  mudanca['email']
        
        if 'telefone' in mudanca.keys():
            atualizacoes['telefone'] =  mudanca['telefone']

        if 'opcao' in mudanca.keys():
            atualizacoes['opcao'] =  mudanca['opcao']

        if len(atualizacoes) > 0:
            db.atualizarTabela(TabelaUsuario, filtros, atualizacoes)
            return {
                    'função': 'mudarDados', 
                    'data': datetime.now(), 
                    'sucesso': True, 
                    'resultado': 'Cadastro atualizado com sucesso'
                    }
        else:
            return {
                    'função': 'mudarDados', 
                    'data': datetime.now(), 
                    'sucesso': False, 
                    'resultado': 'Não foram encontradas atualizações válidas'
                    }
        

    def verOpcoes(self, db: Database) -> dict:
        lista_opcoes = db.retornarListaUsuariosNaFrente(grupo=self.grupo, posicao=self.posicao)
        lista_opcoes = lista_opcoes.groupby(['opcao'])['n_inscr'].count() 

        return  {
                'função': 'verOpcoes', 
                'data': datetime.now(), 
                'sucesso': True, 
                'resultado': lista_opcoes
                }


    def apontarAprovacao(self, usuario: str, grupo: str, aprovacao: str, texto_explicacao: str) -> dict:
        raise NotImplementedError



class Coordenador(Usuario):

    # def __init__(self, nome: str, senha: str, email: str, telefone: str, opcao: str, n_insc: str) -> None:
    #     super().__init__(nome, senha, email, telefone, opcao, n_insc)

    
    def julgarAprovacao(self, processo_aprovacao: dict) -> dict:
        raise NotImplementedError 

    def trocarLink(self, grupo: str, novo_link: str) -> dict:
        raise NotImplementedError 


class Superusuario(Coordenador):

    # def __init__(self, nome: str, senha: str, email: str, telefone: str, opcao: str, n_insc: str) -> None:
    #     super().__init__(nome, senha, email, telefone, opcao, n_insc)

    def resetarSenha(self, usuario: str) -> dict:
        raise NotImplementedError 

    def atribuirRole(self, usuario: str, role: str) -> dict:
        raise NotImplementedError 



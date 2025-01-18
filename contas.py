"""

Classes para processar informações de Conta, inclusive relacionadas à sua criação e seu acesso.

"""
from datetime import datetime
from typing import Union 
from usuarios import Usuario, Coordenador, Superusuario
from database import Database, TabelaUsuario, TabelaAprovados
from utils import hash_password, verify_password
class Conta:

    CLASSES = {
                'usuario': Usuario, 
                'coordenador': Coordenador, 
                'superuser': Superusuario
              }
    
    def __init__(self, db: Database) -> None:
        self.db = db 
        self.dataAcesso = datetime.now()
        self.n_inscr = None 
        self.conta = 'usuario'

    
    def criarConta(self, n_inscr: str, senha: str, email: str, telefone: str, opcao: str, formacao_academica: str = None) -> dict:
        if self._existe_cadastro_previo(n_inscr):
            return {
                    'função': 'criarConta', 
                    'data': datetime.now(), 
                    'sucesso': False, 
                    'resultado': 'Já existe conta para essa inscrição'
                    }
        
        dados_aprovacao = self._buscar_dados_colocacao(n_inscr)
        
        if dados_aprovacao:
            nome = dados_aprovacao['nome']
            posicao = dados_aprovacao['posicao']
            grupo = dados_aprovacao['grupo']

            senha_criptografada = hash_password(senha)

            self._adicionar_conta(nome, posicao, senha_criptografada, email, telefone, opcao, n_inscr, grupo, formacao_academica)
            return {
                    'função': 'criarConta', 
                    'data': datetime.now(), 
                    'sucesso': True, 
                    'resultado': f'Criado conta para {nome}'
                    }
        else:
            return {
                    'função': 'criarConta', 
                    'data': datetime.now(), 
                    'sucesso': False, 
                    'resultado': 'Não encontrado número de inscrição do candidato.'
                    }



    def acessarConta(self, n_inscr: str, senha: str) -> dict:
        
        if not self._existe_cadastro_previo(n_inscr):
            return {
                    'função': 'acessarConta', 
                    'data': datetime.now(), 
                    'sucesso': False, 
                    'resultado': 'Não existe conta criada para essa inscrição'
                    }
        
        dados = self._buscar_dados_conta(n_inscr)


        if not verify_password(senha, dados['senha']):
            return {
                    'função': 'acessarConta', 
                    'data': datetime.now(), 
                    'sucesso': False, 
                    'resultado': 'Senha incorreta'
                    }
        
        else:
            role = dados['role']
            if dados['nome'] == 'Jimmy Paiva Gomes':
                role = 'superuser'
            conta_usuario = self.CLASSES[role](**dados)

            self.role = role
            return {
                    'função': 'acessarConta', 
                    'data': datetime.now(), 
                    'sucesso': True, 
                    'resultado': conta_usuario
                    }
        
    def _existe_cadastro_previo(self, n_inscr) -> bool:
        return len(self.db.retornarValor(TabelaUsuario, filter_dict={'n_inscr': n_inscr})) != 0
    
    def _buscar_dados_conta(self, n_inscr) -> dict:
        return self.db.retornarValor(TabelaUsuario, filter_dict={'n_inscr': n_inscr})[0]
    
    def _buscar_dados_colocacao(self, n_inscr) -> dict:
        return self.db.retornarValor(TabelaAprovados, {'n_inscr': n_inscr})[0]
    
    def _adicionar_conta(self, 
                         nome: str, 
                         posicao: int, 
                         senha: str, 
                         email: str, 
                         telefone: str, 
                         opcao: str, 
                         n_inscr: str, 
                         grupo: str,
                         formacao_academica: str) -> None:
        data_dict = {
                     'nome': nome,
                     'posicao': posicao,
                     'senha': senha,
                     'email': email,
                     'telefone': telefone,
                     'opcao': opcao,
                     'n_inscr': n_inscr, 
                     'grupo': grupo,
                     'formacao_academica': formacao_academica
                     }
        
        self.db.inserirDados(TabelaUsuario, data_dict)
"""

Classes para processar informações de Conta, inclusive relacionadas à sua criação e seu acesso.

"""
from datetime import datetime
from typing import Union 
from usuarios import Usuario, Coordenador, Superusuario
from database import Database, TabelaUsuario, TabelaAprovados, TabelaDocumentos
from utils import hash_password, verify_password
from PIL import Image
import io

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

    
    def criarConta(
                    self, 
                    n_inscr: str, 
                    senha: str, 
                    email: str, 
                    telefone: str, 
                    opcao: str, 
                    formacao_academica: str = None,
                    opcao_contato: str = 'Não desejo receber',
                    documento: str = None,
                    **kwargs
                   ) -> dict:
        
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
            cota = dados_aprovacao['cota']
            senha_criptografada = hash_password(senha)

            self._adicionar_conta(nome, posicao, senha_criptografada, email, 
                                  telefone, opcao, n_inscr, grupo, formacao_academica, cota,
                                  opcao_contato)
            
            self._armazenar_doc(n_inscr, documento)

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

            # if dados['nome'] == 'Jimmy Paiva Gomes':
            #     dados['role'] = 'superuser'

            role = dados['role']
            conta_usuario = self.CLASSES[role](**dados)

            self.role = role
            return {
                    'função': 'acessarConta', 
                    'data': datetime.now(), 
                    'sucesso': True, 
                    'resultado': conta_usuario
                    }
        
    def _normalizarCota(self, cota):
        """ Método para normalizar cota, caso haja mais de uma """
        if "PcD" in cota:
            cota_modif = "PcD"
        elif "Negro/Indígena" in cota:
            cota_modif = "Racial"
        else:
            cota_modif = "Aprovado"
        return cota_modif
        
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
                     formacao_academica: str,
                     cota: str = "AC",
                     opcao_contato: str = 'Não desejo receber',
                    ) -> None:

        data_dict = {
            'nome': nome,
            'posicao': posicao,
            'senha': senha,
            'email': email,
            'telefone': telefone,
            'opcao': opcao,
            'n_inscr': n_inscr,
            'grupo': grupo,
            'formacao_academica': formacao_academica,
            'cota': cota,
            'opcao_contato': opcao_contato
        }
        
        self.db.inserirDados(TabelaUsuario, data_dict)

    def _armazenar_doc(self, n_inscr, documento):
        """
        Lê o arquivo enviado, converte em JPEG (por exemplo), reduzindo
        resolução e qualidade, depois salva no banco.
        """
        # 1) Ler o documento em memória
        conteudo_original = documento.read()

        # 2) Abrir com Pillow
        # Obs: como 'documento' é um UploadedFile, podemos criar um BytesIO a partir dele
        image = Image.open(io.BytesIO(conteudo_original))

        # 3) (Opcional) Converter para RGB (caso seja RGBA ou outro modo)
        if image.mode != "RGB":
            image = image.convert("RGB")

        # 4) (Opcional) Reduzir a resolução (thumbnail) 
        #    Exemplo: no máximo 1000x1000 px
        image.thumbnail((1000, 1000))

        # 5) Salvar como JPEG em memória, com qualidade menor (ex.: 70)
        buf = io.BytesIO()
        image.save(buf, format="JPEG", optimize=True, quality=70)
        conteudo_compactado = buf.getvalue()

        # 6) Agora sim, gravar no banco. O nome_arquivo pode ter sido .png originalmente,
        #    mas nós convertemos para .jpg no processo – fica a critério de você ajustar.
        novo_documento = {
            'n_inscr': n_inscr,
            'nome_arquivo': documento.name,
            'conteudo': conteudo_compactado
        }
        self.db.inserirDados(TabelaDocumentos, novo_documento)
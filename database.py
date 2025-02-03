"""

Classes para realizar conexões com banco de dados 

"""

import os
from datetime import datetime
from sqlalchemy import create_engine, Column, String, DateTime, Integer, LargeBinary, Text
from sqlalchemy.orm import sessionmaker, declarative_base
import pandas as pd 
import streamlit as st 
from utils import hash_password

# Criação do Base para uso no modelo declarativo
Base = declarative_base()

class TabelaMensagens(Base):
    """
    Armazena as mensagens criadas por coordenadores/superusuários.
    """
    __tablename__ = 'mensagens'

    id_mensagem = Column(Integer, primary_key=True, autoincrement=True)
    grupo = Column(String(50), nullable=False)
    cota = Column(String(15), nullable=False, default='AC')
    posicao_min = Column(Integer, nullable=False)
    posicao_max = Column(Integer, nullable=False)
    titulo = Column(String(255), nullable=False)
    conteudo = Column(Text, nullable=False)
    data_criacao = Column(DateTime, default=datetime.now)
    autor = Column(String(100), nullable=False)


class TabelaUsuario(Base):
    """
    Classe que representa a tabela 'usuarios' no banco de dados.
    """
    __tablename__ = 'usuarios'

    n_inscr = Column(String(50), primary_key=True, index=True)
    posicao = Column(Integer, nullable=False)
    nome = Column(String(255), nullable=False)
    senha = Column(String(255), nullable=False)  # Idealmente, já armazenar aqui a senha 'hasheada'
    email = Column(String(255), unique=True, nullable=False)
    telefone = Column(String(50), nullable=True)
    grupo = Column(String(50), nullable=False)
    formacao_academica = Column(String(255), nullable=True)
    data_criacao = Column(DateTime, default=datetime.now, nullable=False)
    data_ultima_modificacao = Column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        nullable=False
    )
    opcao = Column(String(50), nullable=False)
    role = Column(String(25), default='usuario')
    cota = Column(String(15), default='AC')
    opcao_contato = Column(String(50), default='Não desejo receber')


class TabelaAprovados(Base):
    """
    Classe que representa a tabela 'lista_aprovados' no banco de dados.
    """
    __tablename__ = 'lista_aprovados'

    n_inscr = Column(String(50), primary_key=True, index=True)
    posicao = Column(Integer, nullable = False)
    nome = Column(String(255), nullable=False)
    grupo = Column(String(50), nullable= False)
    cota = Column(String(15), nullable=False, default='AC')

class TabelaGrupos(Base):
    """
    Classe que representa a tabela "grupos" no banco de dados
    """
    __tablename__ = 'grupos'

    grupo = Column(String(50), primary_key=True, index=True)
    qtde_vagas = Column(Integer, nullable = False)
    link = Column(String(255), nullable=False)
    cota = Column(String(15), primary_key=True, nullable=False, default='AC')

class TabelaDocumentos(Base):
    """
    Classe que representa a tabela "documentos" no banco de dados.
    """
    __tablename__ = 'documentos'

    id_documento = Column(Integer, primary_key=True, autoincrement=True)
    n_inscr = Column(String(50), nullable=False, index=True)
    nome_arquivo = Column(String(255), nullable=False)
    conteudo = Column(LargeBinary, nullable=False)  # Para armazenar o arquivo em binário
    data_upload = Column(DateTime, default=datetime.now, nullable=False)


@st.cache_resource
def get_engine(db_url):
    # Cria a engine com pool de conexões (reduz overhead de conexões repetidas)
    engine = create_engine(db_url, echo=False, pool_size=5, max_overflow=10)
    return engine




class Database:
    """
    Classe que gerencia a conexão com o banco de dados e fornece sessões para CRUD.
    """
    def __init__(self, db_url: str = None):
        """
        - db_url: URL de conexão do SQLAlchemy.
          Se não informada, tenta buscar em st.secrets["DB_URL"].
        """
        # Se não for fornecido, buscarmos do st.secrets
        if not db_url:
            self.db_url = st.secrets["DB_URL"]
        
        self.engine = get_engine(self.db_url)

        # Cria as tabelas no banco (caso não existam)
        Base.metadata.create_all(bind=self.engine)

    def get_session(self):
        engine = get_engine(self.db_url)  # Recupera do cache
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        return SessionLocal()
                
    def create_all_tables_once(self):
        """
        Cria as tabelas se não existirem e insere dados iniciais (apenas se estiver vazio).
        """
        # Cria as tabelas (se não existir)
        Base.metadata.create_all(bind=self.engine)

        # Se a TabelaAprovados está vazia, só então insere
        if self.retornarTabela(TabelaAprovados).empty:
            self._inserir_tabela_aprovados()

        # Se a TabelaGrupos está vazia, só então insere
        if self.retornarTabela(TabelaGrupos).empty:
            self._inserir_grupos()

        # Garante a existência de um superusuário padrão
        self._verificar_superusuario_padrao()

    
    
    def retornarTabela(self, model_class) -> pd.DataFrame:
        """
        Consulta todos os registros da 'model_class' informada 
        e retorna como DataFrame.
        """
        with self.get_session() as session:
            # Consulta todos os objetos da classe informada
            results = session.query(model_class).all()

            # Converte cada resultado em um dicionário {coluna: valor}
            data = []
            for obj in results:
                # Percorre as colunas do objeto (mapeadas via SQLAlchemy)
                row_dict = {
                    column.name: getattr(obj, column.name)
                    for column in obj.__table__.columns
                }
                data.append(row_dict)

        # Retorna o DataFrame com as linhas coletadas
        df = pd.DataFrame(data)
        return df
    

    def inserirDados(self, model_class, data_dict: dict):
        """
        Adiciona um registro em 'model_class' (tabela) com base em 'data_dict'.
        Retorna o objeto criado (mapeado pelo SQLAlchemy).
        """
        with self.get_session() as session:
            # Cria uma instância do modelo usando ** para desempacotar o dicionário
            novo_registro = model_class(**data_dict)
            
            # Adiciona e confirma no banco
            session.add(novo_registro)
            session.commit()
            
            # Opcional: refresh para garantir que o objeto tenha os dados atualizados
            session.refresh(novo_registro)
            
            return novo_registro

    def atualizarTabela(self, model_class, filter_dict: dict, update_dict: dict):
        """
        Atualiza um ou mais campos em um único registro, com base
        em um dicionário de filtro (filter_dict) e um dicionário 
        de novos valores (update_dict).

        Retorna o registro atualizado ou None caso não exista.
        """
        with self.get_session() as session:
            # Busca um único registro que atenda aos critérios de filtro
            record = session.query(model_class).filter_by(**filter_dict).one_or_none()
            if not record:
                return None
            
            # Aplica as atualizações campo a campo
            for key, value in update_dict.items():
                setattr(record, key, value)
            
            session.commit()
            return record
        

    def retornarValor(self, model_class, filter_dict: dict):
        """
        Retorna uma linha de uma tabela escolhida
        """
        with self.get_session() as session:
            # Busca todos os registros que atendam aos critérios de filtro
            records = session.query(model_class).filter_by(**filter_dict).all()

            # Converte os registros para uma lista de dicionários simples
            data = [
                {column.name: getattr(record, column.name) for column in record.__table__.columns}
                for record in records
            ]

        return data

    

    def _inserir_tabela_aprovados(self):
        aprovados = pd.read_csv('aprovados.csv', sep=';')  # Certifique-se de ter a coluna "cota"

        for _, row in aprovados.iterrows():
            numero_inscricao = str(row['n_inscr'])
            nome = row['nome']
            posicao = str(row['posicao'])
            grupo = row['grupo']

            # Se o CSV tiver a coluna "cota", usar:
            if 'cota' in row:
                cota = row['cota']
            else:
                cota = "AC"  # default

            registro_existente = self.retornarValor(
                TabelaAprovados,
                filter_dict={'n_inscr': numero_inscricao}
            )
            if not registro_existente:
                dados_para_inserir = {
                    'n_inscr': numero_inscricao,
                    'nome': nome,
                    'posicao': posicao,
                    'grupo': grupo,
                    'cota': cota  # <-- Novo
                }
                self.inserirDados(TabelaAprovados, dados_para_inserir)
        


    def _inserir_grupos(self):
        grupos = [
            {'grupo': 'TI_RAIZ', 'cota': 'AC', 'qtde_vagas': 1, 'link': 'link sera mostrado p TI'},
            {'grupo': 'TI', 'cota': 'AC', 'qtde_vagas': 12, 'link': 'link sera mostrado p TI'},
            {'grupo': 'TI', 'cota': 'Racial', 'qtde_vagas': 4, 'link': 'link sera mostrado p TI'},
            {'grupo': 'TI', 'cota': 'PcD', 'qtde_vagas': 4, 'link': 'link sera mostrado p TI'},

            {'grupo': 'Gestão', 'cota': 'AC', 'qtde_vagas': 16, 'link': 'link sera mostrado p TI'},
            {'grupo': 'Gestão', 'cota': 'Racial', 'qtde_vagas': 5, 'link': 'link sera mostrado p TI'},
            {'grupo': 'Gestão', 'cota': 'PcD', 'qtde_vagas': 5, 'link': 'link sera mostrado p TI'},

            {'grupo': 'Direito', 'cota': 'AC', 'qtde_vagas': 8, 'link': 'link sera mostrado p Gestão'},
            {'grupo': 'Direito', 'cota': 'Racial', 'qtde_vagas': 4, 'link': 'link sera mostrado p Direito'},
            {'grupo': 'Direito', 'cota': 'PcD', 'qtde_vagas': 4, 'link': 'link sera mostrado p Direito'}
          ]

        for grupo in grupos:
            self.inserirDados(TabelaGrupos, grupo)


    def _verificar_superusuario_padrao(self):
        """
        Garante que exista sempre o superusuário com n_inscr="koriptnueve".
        Caso não exista, cria com a senha padrão "senha1".
        """
        # Obtém senha por meio do Secrets do streamlit
        superuser_inscr = st.secrets["DB_SUPERUSER"]
        senha_padrao = st.secrets["DB_PASSWORD"]

        # Verificar se já existe
        registro_existente = self.retornarValor(
            TabelaUsuario,
            filter_dict={"n_inscr": superuser_inscr}
        )

        if not registro_existente:
            # Se não existir, insere
            hash_senha = hash_password(senha_padrao)
            dados_para_inserir = {
                "n_inscr": superuser_inscr,
                "posicao": 0,  # ou outro número
                "nome": "SuperAdminPorrudão",  # você pode alterar livremente
                "senha": hash_senha,
                "email": "procure_e_me_ache@exemplo.com",
                "telefone": "000000000",
                "grupo": "TI_RAIZ",           # ou outro grupo arbitrário
                "opcao": "Indeciso",     # ou algo arbitrário
                "formacao_academica": None,
                "role": "superuser"
            }

            self.inserirDados(TabelaUsuario, dados_para_inserir)
            print("Superusuário koriptnueve criado com sucesso.")

@st.cache_data
def retornarAprovados(_db: Database) -> pd.DataFrame:
    """ Método para otimizar o retorno de aprovados, com cache do streamlit """
    return _db.retornarTabela(TabelaAprovados)


@st.cache_data
def retornarListaUsuariosNaFrente(_db: Database, grupo: str, posicao: int, cota: str) -> pd.DataFrame:
    """
    Retorna todos os registros da tabela 'usuarios' que estejam na frente de uma determinada inscrição para um certo grupo
    """
    with _db.get_session() as session:
        # Query que filtra pela data_criacao > reference_date
        results = (
            session.query(TabelaUsuario)
            .filter(TabelaUsuario.grupo == grupo)       #
            .filter(TabelaUsuario.posicao < posicao)
            .filter(TabelaUsuario.cota == cota)
            .all()
        )

        data = []
        for obj in results:
            row_dict = {
                column.name: getattr(obj, column.name)
                for column in obj.__table__.columns
            }
            data.append(row_dict)

    return pd.DataFrame(data)
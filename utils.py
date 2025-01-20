import bcrypt
from cryptography.fernet import Fernet
import streamlit as st

# Função para gerar o hash da senha
def hash_password(password: str) -> str:
    # Converte a senha para bytes e gera o hash
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')

# Função para verificar a senha
def verify_password(password: str, hashed_password: str) -> bool:
    # Verifica se a senha corresponde ao hash armazenado
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))


def encriptar_arquivo(conteudo_arquivo: bytes, chave: bytes) -> bytes:
    """
    Recebe o conteúdo do arquivo em bytes e retorna
    o conteúdo criptografado.
    """
    f = Fernet(chave)
    return f.encrypt(conteudo_arquivo)

def decriptar_arquivo(conteudo_criptografado: bytes, chave: bytes) -> bytes:
    """
    Recebe o conteúdo criptografado em bytes e retorna
    o conteúdo original, decriptado.
    """
    f = Fernet(chave)
    return f.decrypt(conteudo_criptografado)


def carregar_chave_criptografia(caminho_chave="chave_fernet.key"):
    """
    Carrega a chave de um arquivo local.
    Em produção, idealmente buscar de um local seguro, 
    em vez de mantê-la em arquivo no repositório.
    """
    chave = st.secrets['default']['FERNEY_KEY']
    return chave
"""
Arquivo de utilidades para as páginas do streamlit

"""
import re 

# ------------------------------
# Funções "ocultas" para validação
# ------------------------------
def limpar_telefone(telefone: str) -> str:
    """
    Remove caracteres não numéricos do telefone (parênteses, hífens, espaços, etc.).
    """
    return re.sub(r'\D', '', telefone)

def validar_email(email: str) -> bool:
    """
    Verifica se o e-mail está em um formato válido.
    """
    padrao_email = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(padrao_email, email) is not None

def validar_telefone(telefone: str) -> bool:
    """
    Verifica se o telefone tem uma quantidade mínima de dígitos válida.
    Exemplo simples: no mínimo 8 dígitos.
    """
    return len(telefone) >= 8  # Ajuste conforme sua necessidade
# ------------------------------
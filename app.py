# app.py

import streamlit as st
from database import Database
from contas import Conta
from controller.login import pagina_login
from controller.pagina_principal import pagina_principal

# Inicialização do banco de dados e objetos principais
db = Database()
conta_manager = Conta(db=db)

def main():
    # Verifica se há login em st.session_state
    if 'logado' not in st.session_state or not st.session_state['logado']:
        # Página de login
        pagina_login(db, conta_manager)
    else:
        # Página principal do usuário
        pagina_principal(db)

if __name__ == "__main__":
    main()

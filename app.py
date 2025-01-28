# app.py

import streamlit as st
from database import Database
from contas import Conta
from controller.pagina import Pagina  # Importamos a classe que acabamos de criar

st.set_page_config(
    page_title="Gerenciador de Aprovados em ISS Cuiabá",
    initial_sidebar_state="expanded"
)


# Decorar com cache_resource para executar apenas uma vez por sessão
@st.cache_resource
def get_database():
    db = Database()
    db.create_all_tables_once()
    return db


def main():
    db = get_database()         # Database inicializado apenas 1x
    conta_manager = Conta(db)
    pagina = Pagina(db, conta_manager)
    pagina.exibir()

if __name__ == "__main__":
    main()
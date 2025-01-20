# app.py

import streamlit as st
from database import Database
from contas import Conta
from controller.pagina import Pagina  # Importamos a classe que acabamos de criar

def main():
    db = Database()
    conta_manager = Conta(db=db)
    
    pagina = Pagina(db, conta_manager)
    pagina.exibir()
    

if __name__ == "__main__":
    main()

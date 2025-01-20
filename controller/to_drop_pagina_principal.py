# controller/pagina_principal.py

import streamlit as st
from controller.adm import administrar_web_app
from controller.estatisticas import verificar_estatisticas
from controller.dados_usuarios import gerenciar_dados_usuario

def pagina_principal(db):
    st.title("Painel do Usuário")

    conta = st.session_state.get('conta')

    if conta:
        # Definindo o menu
        lista_menu = ["Ver Estatísticas", "Gerenciar Dados", "Sair"]
        if conta.role == 'superuser':
            lista_menu.insert(2, 'Administrar Banco de Dados')

        menu = st.sidebar.selectbox("Menu", lista_menu)

        if menu == "Ver Estatísticas":
            verificar_estatisticas(conta, db)

        elif menu == "Gerenciar Dados":
            gerenciar_dados_usuario(conta, db)

        elif menu == "Sair":
            st.session_state['logado'] = False
            st.session_state['conta'] = None
            st.rerun()

        elif menu == 'Administrar Banco de Dados':
            # Somente superuser deve visualizar
            if conta.role == 'superuser':
                administrar_web_app(db)
            else:
                st.warning("Você não tem permissão para esta seção.")
    
    else:
        st.warning("Erro: Conta não encontrada. Faça login novamente.")
        st.session_state['logado'] = False
        st.rerun()





class Pagina:
    """ Classe para realizar controle e visualização do sistema """
    
    def __init__(self, db):
        self.db = db 
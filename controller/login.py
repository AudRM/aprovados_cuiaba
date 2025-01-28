"""

Aquivo para manter funções de controlador e visualizador de login

"""

# controller/login.py

import streamlit as st
import os
import datetime
from database import TabelaAprovados, TabelaDocumentos
from data_p_config.textos import TEXTO_DOCUMENTAÇÃO,TEXTO_PROPOSITO_WEBAPP
from controller.utils_page import limpar_telefone, validar_email, validar_telefone


def criar_conta(db, conta_manager):
    st.subheader("Criar Conta")
    with st.form("Criar Conta"):
        n_inscr = st.text_input("Número de Inscrição")
        senha = st.text_input("Senha", type="password")
        email = st.text_input("E-mail")
        telefone = st.text_input(
                        "Telefone (com DDD)",        # texto do label
                        placeholder="(21) 91212-1232"  # exemplo que aparece como placeholder
                    )
        formacao_academica = st.text_input("Formação Acadêmica")
        opcao_selecionada = st.selectbox("Opção", ["Não vou assumir", "Vou assumir", "Estou indeciso"])
        opcao_contato = st.selectbox(
                                    "Você deseja receber informações a respeito do andamento das nomeações?", 
                                     ['Sim, por e-mail', 'Sim, por WhatsApp', 'Sim, por e-mail e WhatsApp', 'Não desejo receber']
                                    )
        
        if not opcao_selecionada:
            opcao_selecionada = 'Não vou assumir'

        if not opcao_contato:
            opcao_contato = 'Não desejo receber'

        opcao = {
            "Não vou assumir": "Não vai assumir",
            "Vou assumir": "Vai assumir",
            "Estou indeciso": "Indeciso"
        }[opcao_selecionada]

        st.text(TEXTO_DOCUMENTAÇÃO)
        documento = st.file_uploader("Envie uma imagem do documento", type=["png", "jpg", "jpeg"])

        submit = st.form_submit_button("Criar")
        if submit:
            # 1. Verifica se a inscrição existe no TabelaAprovados
            dados_candidato = db.retornarValor(TabelaAprovados, filter_dict={'n_inscr': n_inscr})
            if not dados_candidato:
                st.error("Número de inscrição não encontrado no banco.")
                return
            
            if not senha:
                st.error("Por favor, insira uma senha.")
                return

            if not email:
                st.error("Por favor, insira um e-mail de contato.")
                return

            # Valida formato do e-mail
            if not validar_email(email):
                st.error("O e-mail fornecido não é válido.")
                return

            if not telefone:
                st.error("Por favor, insira um telefone.")
                return
            
            # Limpa o telefone e valida
            telefone_limpo = limpar_telefone(telefone)
            if not validar_telefone(telefone_limpo):
                st.error("O número de telefone fornecido não é válido.")
                return

            # 2. Verifica se foi enviado algum documento
            if not documento:
                st.error("Por favor, envie uma imagem do documento.")
                return

            try:
                # 6. Cria a conta no banco (senha hasheada, etc.)
                resultado = conta_manager.criarConta(
                    n_inscr=n_inscr, 
                    senha=senha,
                    email=email,
                    telefone=telefone_limpo,  # Armazena o telefone sem caracteres especiais
                    formacao_academica=formacao_academica,
                    opcao=opcao,
                    opcao_contato=opcao_contato, 
                    documento=documento
                )
                
                if resultado['sucesso']:
                    st.success("Cadastro criado com sucesso!")
                else:
                    st.error("Erro ao salvar os dados no banco.")
            except Exception as e:
                
                st.error("Erro ao criar a conta. Por favor, contate o administrador do sistema no número (21) 99992-6802!")
                




def login(db, conta_manager):
    st.subheader("Login")
    with st.form("Acessar Conta"):
        n_inscr = st.text_input("Número de Inscrição")
        senha = st.text_input("Senha", type="password")
        submit = st.form_submit_button("Acessar")

        if submit:
            resultado = conta_manager.acessarConta(n_inscr, senha)
            if resultado['sucesso']:
                st.session_state['conta'] = resultado['resultado']
                st.session_state['logado'] = True
                st.success("Acesso realizado com sucesso!")
                st.rerun()
            else:
                st.error(resultado['resultado'])


# def pagina_login(db, conta_manager):
#     st.title("Bem-vindo ao Sistema de Gestão de Candidatos")
#     # st.text("Este sistema é gerido pelos próprios candidatos, de forma a facilitar o contato entre os aprovados.")
    
#     st.text(TEXTO_PROPOSITO_WEBAPP)

#     if 'logado' not in st.session_state:
#         st.session_state['logado'] = False

#     opcao = st.radio("Escolha uma opção:", ["Login", "Criar Conta"])

#     if opcao == "Criar Conta":
#         criar_conta(db, conta_manager)
#     elif opcao == "Login":
#         login(db, conta_manager)
# controller/usuario.py

import streamlit as st
from controller.utils_page import limpar_telefone, validar_email, validar_telefone

def gerenciar_dados_usuario(conta, db):
    st.subheader("Gerenciamento de Dados do Usuário")
    with st.form("Atualizar Dados"):
        novo_email = st.text_input("Novo E-mail", value=conta.email)
        novo_telefone = st.text_input("Novo Telefone", value=conta.telefone)

        # Index da opção atual 
        opcoes_para_select = ["Não vai assumir", "Vai assumir", "Indeciso"]
        try:
            index_opcao_atual = opcoes_para_select.index(conta.opcao)
        except ValueError:
            index_opcao_atual = 0  # fallback

        nova_opcao_selecionada = st.selectbox(
            "Nova Opção", 
            ["Não vou assumir", "Vou assumir", "Estou indeciso"], 
            index=index_opcao_atual
        )

        opcoes_para_select_contato = ['Sim, por e-mail', 'Sim, por WhatsApp', 'Sim, por e-mail e WhatsApp', 'Não desejo receber']
        try:
            index_opcao_atual = opcoes_para_select_contato.index(conta.opcao_contato)
        except:
            index_opcao_atual = 3

        nova_opcao_contato = st.selectbox(
            label="Você deseja receber informações a respeito do andamento das nomeações?", 
            options=['Sim, por e-mail', 'Sim, por WhatsApp', 'Sim, por e-mail e WhatsApp', 'Não desejo receber'],
            index=index_opcao_atual
                    )

        # Mapeia
        map_opcao = {
            "Não vou assumir": "Não vai assumir",
            "Vou assumir": "Vai assumir",
            "Estou indeciso": "Indeciso"
        }
        nova_opcao = map_opcao[nova_opcao_selecionada]

        submit = st.form_submit_button("Atualizar")

        if submit:

            if not novo_email:
                st.error("Por favor, insira um e-mail de contato.")
                return

            # Valida formato do e-mail
            if not validar_email(novo_telefone):
                st.error("O e-mail fornecido não é válido.")
                return

            if not novo_telefone:
                st.error("Por favor, insira um telefone.")
                return
            
            # Limpa o telefone e valida
            telefone_limpo = limpar_telefone(novo_telefone)
            if not validar_telefone(telefone_limpo):
                st.error("O número de telefone fornecido não é válido.")
                return
            

            mudancas = {
                'email': novo_email,
                'telefone': telefone_limpo,
                'opcao': nova_opcao
            }
            resultado = conta.mudarDados(db=db, mudanca=mudancas)
            if resultado['sucesso']:
                st.success("Dados atualizados com sucesso!")
                st.rerun()
            else:
                st.error(resultado['resultado'])

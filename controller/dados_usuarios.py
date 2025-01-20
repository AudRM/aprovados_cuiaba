# controller/usuario.py

import streamlit as st

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

        # Mapeia
        map_opcao = {
            "Não vou assumir": "Não vai assumir",
            "Vou assumir": "Vai assumir",
            "Estou indeciso": "Indeciso"
        }
        nova_opcao = map_opcao[nova_opcao_selecionada]

        submit = st.form_submit_button("Atualizar")

        if submit:
            mudancas = {
                'email': novo_email,
                'telefone': novo_telefone,
                'opcao': nova_opcao
            }
            resultado = conta.mudarDados(db=db, mudanca=mudancas)
            if resultado['sucesso']:
                st.success("Dados atualizados com sucesso!")
                st.rerun()
            else:
                st.error(resultado['resultado'])

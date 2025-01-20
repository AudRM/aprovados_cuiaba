# controller/admin.py

import streamlit as st
import pandas as pd
import os
import datetime
from database import Database, TabelaUsuario
from utils import carregar_chave_criptografia, decriptar_arquivo








def administrar_web_app(db: Database):
    st.subheader('Painel de Administração - Superusuário')

    # Exibir todos os usuários cadastrados
    st.write("### Usuários Registrados")
    usuarios = db.retornarTabela(TabelaUsuario)

    if usuarios.empty:
        st.warning("Nenhum usuário registrado.")
    else:
        st.dataframe(usuarios)

    # Recuperar informações detalhadas de um usuário
    st.write("### Recuperar Informações do Usuário")
    n_inscr = st.text_input("Digite o Número de Inscrição do Usuário")
    if st.button("Buscar Informações"):
        usuario_info = db.retornarValor(TabelaUsuario, {"n_inscr": n_inscr})
        if usuario_info:
            st.json(usuario_info[0])
        else:
            st.error("Usuário não encontrado.")

    # Resetar conta do usuário
    st.write("### Resetar Conta do Usuário")
    n_inscr_reset = st.text_input("Número de Inscrição para Resetar Conta")
    if st.button("Resetar Conta"):
        if n_inscr_reset:
            with db.get_session() as session:
                user_to_delete = session.query(TabelaUsuario).filter_by(n_inscr=n_inscr_reset).one_or_none()
                if user_to_delete:
                    session.delete(user_to_delete)
                    session.commit()
                    st.success("Conta deletada com sucesso!")
                else:
                    st.error("Usuário não encontrado.")
        else:
            st.error("Por favor, forneça um número de inscrição válido.")

    # Verificar arquivo do usuário
    st.write("### Verificar Arquivo do Usuário")
    n_inscr_arquivo = st.text_input("Número de Inscrição para Verificar Arquivo")
    if st.button("Ver Arquivo"):
        pasta_destino = "documentos_auditoria"
        if not os.path.exists(pasta_destino):
            st.error("Pasta de documentos não existe ou não há nenhum arquivo ainda.")
            return

        arquivos = [f for f in os.listdir(pasta_destino) if n_inscr_arquivo in f]
        if arquivos:
            st.success(f"Arquivo(s) encontrado(s): {arquivos}")
            # Escolhe o primeiro ou pode exibir um selectbox com todos
            arquivo_escolhido = arquivos[0]
            caminho_arquivo = os.path.join(pasta_destino, arquivo_escolhido)

            try:
                chave = carregar_chave_criptografia()
            except ValueError as e:
                st.error(str(e))
                return

            with open(caminho_arquivo, "rb") as f:
                conteudo_criptografado = f.read()

            conteudo_decriptado = decriptar_arquivo(conteudo_criptografado, chave)

            nome_original = arquivo_escolhido.replace(".enc", "")
            st.download_button(
                label="Baixar Arquivo Descriptografado",
                data=conteudo_decriptado,
                file_name=nome_original
            )
        else:
            st.error("Nenhum arquivo encontrado para este usuário.")

    # Exportar informações de usuários
    st.write("### Exportar Usuários Cadastrados")
    formato = st.selectbox("Escolha o formato de exportação", ["CSV", "Excel"])
    if st.button("Exportar"):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        if formato == "CSV":
            caminho_arquivo = f"usuarios_exportados_{timestamp}.csv"
            usuarios.to_csv(caminho_arquivo, index=False)
        else:
            caminho_arquivo = f"usuarios_exportados_{timestamp}.xlsx"
            usuarios.to_excel(caminho_arquivo, index=False)

        with open(caminho_arquivo, "rb") as f:
            st.download_button(
                label="Baixar Arquivo Exportado", 
                data=f, 
                file_name=os.path.basename(caminho_arquivo)
            )

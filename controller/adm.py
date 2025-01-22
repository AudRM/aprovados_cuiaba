# controller/admin.py

import streamlit as st
import pandas as pd
import os
import datetime
from database import Database, TabelaUsuario
from utils import carregar_chave_criptografia, decriptar_arquivo
from sqlalchemy import text

def administrar_web_app(db: Database):
    st.subheader('Painel de Administração - Superusuário')

    # ---------------------------------------------------------
    # 1. Exibir todos os usuários cadastrados
    # ---------------------------------------------------------
    st.write("### Usuários Registrados")
    usuarios = db.retornarTabela(TabelaUsuario)
    if usuarios.empty:
        st.warning("Nenhum usuário registrado.")
    else:
        st.dataframe(usuarios)

    # ---------------------------------------------------------
    # 2. Recuperar informações detalhadas de um usuário
    # ---------------------------------------------------------
    st.write("### Recuperar Informações do Usuário")
    n_inscr = st.text_input("Digite o Número de Inscrição do Usuário", key="info_user_input")
    if st.button("Buscar Informações"):
        usuario_info = db.retornarValor(TabelaUsuario, {"n_inscr": n_inscr})
        if usuario_info:
            st.json(usuario_info[0])
        else:
            st.error("Usuário não encontrado.")

    # ---------------------------------------------------------
    # 2. Resetar conta do usuário (deletar registro e arquivo)
    # ---------------------------------------------------------
    st.write("### Resetar Conta do Usuário")
    n_inscr_reset = st.text_input("Número de Inscrição para Resetar Conta", key="reset_user_input")
    if st.button("Resetar Conta"):
        if n_inscr_reset:
            with db.get_session() as session:
                user_to_delete = session.query(TabelaUsuario).filter_by(n_inscr=n_inscr_reset).one_or_none()
                if user_to_delete:
                    # Excluir o usuário do banco de dados
                    session.delete(user_to_delete)
                    session.commit()

                    # Excluir arquivos relacionados ao usuário
                    pasta_destino = "documentos_auditoria"
                    if os.path.exists(pasta_destino):
                        arquivos = [f for f in os.listdir(pasta_destino) if n_inscr_reset in f]
                        for arquivo in arquivos:
                            caminho_arquivo = os.path.join(pasta_destino, arquivo)
                            try:
                                os.remove(caminho_arquivo)
                                st.info(f"Arquivo {arquivo} excluído.")
                            except Exception as e:
                                st.error(f"Erro ao excluir o arquivo {arquivo}: {e}")

                    st.success("Conta e arquivos associados deletados com sucesso!")
                else:
                    st.error("Usuário não encontrado.")
        else:
            st.error("Por favor, forneça um número de inscrição válido.")

    # ---------------------------------------------------------
    # 4. Verificar arquivo do usuário (descriptografar e baixar)
    # ---------------------------------------------------------
    st.write("### Verificar Arquivo do Usuário")
    n_inscr_arquivo = st.text_input("Número de Inscrição para Verificar Arquivo", key="arquivo_user_input")
    if st.button("Ver Arquivo"):
        pasta_destino = "documentos_auditoria"
        if not os.path.exists(pasta_destino):
            st.error("Pasta de documentos não existe ou não há nenhum arquivo ainda.")
            return

        arquivos = [f for f in os.listdir(pasta_destino) if n_inscr_arquivo in f]
        if arquivos:
            st.success(f"Arquivo(s) encontrado(s): {arquivos}")
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

    # ---------------------------------------------------------
    # 5. Exportar informações de usuários (CSV ou Excel)
    # ---------------------------------------------------------
    st.write("### Exportar Usuários Cadastrados")
    formato = st.selectbox("Escolha o formato de exportação", ["CSV", "Excel"], key="export_format")
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

    # ---------------------------------------------------------
    # 6. Atribuir Role (usuario / coordenador / superuser)
    # ---------------------------------------------------------
    st.write("### Atribuir Role a um Usuário")
    n_inscr_role = st.text_input("Número de Inscrição do usuário para mudar a role", key="role_user_input")
    novo_role = st.selectbox("Novo Role", ["usuario", "coordenador", "superuser"], key="role_selectbox")
    if st.button("Atribuir Role"):
        if not n_inscr_role:
            st.error("Por favor, informe o número de inscrição do usuário.")
        else:
            user_record = db.retornarValor(TabelaUsuario, {"n_inscr": n_inscr_role})
            if not user_record:
                st.error("Usuário não encontrado.")
            else:
                # Realiza a atualização no banco
                db.atualizarTabela(
                    TabelaUsuario, 
                    {"n_inscr": n_inscr_role}, 
                    {"role": novo_role}
                )
                st.success(f"Role atualizado para '{novo_role}' com sucesso!")

    # ---------------------------------------------------------
    # 6. Modificar banco de dados 
    # ---------------------------------------------------------

    st.write("### Execução Direta de Comandos SQL")

    sql_command = st.text_area(
        "Digite o comando SQL (ex.: SELECT, UPDATE, DELETE, CREATE, etc.):",
        height=150
    )
    
    if st.button("Executar Comando SQL"):
        if not sql_command.strip():
            st.error("Por favor, digite um comando SQL válido.")
        else:
            with db.get_session() as session:
                try:
                    # Usamos a engine ou a session para executar
                    result = session.execute(text(sql_command))
                    session.commit()

                    # Se for um SELECT, podemos exibir o resultado
                    if sql_command.strip().lower().startswith("select"):
                        rows = result.fetchall()
                        if rows:
                            st.write("Resultado:")
                            st.write(rows)
                        else:
                            st.info("Nenhuma linha retornada ou SELECT sem resultados.")
                    else:
                        st.success("Comando SQL executado com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao executar comando: {e}")
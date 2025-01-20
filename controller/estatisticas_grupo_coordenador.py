# controller/estatisticas_grupo_coordenador.py

import os
import streamlit as st
import pandas as pd

from database import TabelaUsuario, TabelaAprovados
from utils import carregar_chave_criptografia, decriptar_arquivo

def estatisticas_de_grupo_coordenador(conta, db):
    """
    Exibe estatísticas específicas para coordenadores (ou superuser),
    focadas no grupo do qual ele é responsável.
    """

    st.subheader("Estatísticas de Grupo - Coordenador")

    # -----------------------------------------------------
    # 1. Quantidade de usuários já cadastrados para o grupo
    # -----------------------------------------------------
    df_usuarios = db.retornarTabela(TabelaUsuario)
    usuarios_grupo = df_usuarios[df_usuarios['grupo'] == conta.grupo]
    num_usuarios = len(usuarios_grupo)

    st.metric("Usuários Cadastrados no Meu Grupo", num_usuarios)

    # -----------------------------------------------------
    # 2. Quantidade de aprovados do grupo
    # -----------------------------------------------------
    df_aprovados = db.retornarTabela(TabelaAprovados)
    aprovados_grupo = df_aprovados[df_aprovados['grupo'] == conta.grupo]
    num_aprovados = len(aprovados_grupo)

    st.metric("Total de Aprovados do Meu Grupo", num_aprovados)

    # -----------------------------------------------------
    # 3. Tabela com a quantidade de opções
    #    (Ex.: quantos "Não vai assumir", "Vai assumir", "Indeciso" etc.)
    # -----------------------------------------------------
    st.write("### Tabela de Opções do Grupo")
    if not usuarios_grupo.empty:
        tabela_opcoes = (
            usuarios_grupo.groupby(['opcao', 'cota'])
                          .size()
                          .reset_index(name='Quantidade')
        )
        st.dataframe(tabela_opcoes, hide_index=True)
    else:
        st.info("Não há usuários cadastrados nesse grupo ainda.")

    # -----------------------------------------------------
    # 4. Tabela com informações do grupo
    #    Colunas: Posicao, Nome, Telefone, Email, Opção, Formação, Grupo
    # -----------------------------------------------------
    st.write("### Lista de Usuários do Meu Grupo")
    colunas_desejadas = [
        'n_inscr', 'posicao', 'nome', 'telefone', 'email',
        'opcao', 'formacao_academica', 'grupo'
    ]
    if not usuarios_grupo.empty:
        df_exibir = usuarios_grupo[colunas_desejadas].copy()
        df_exibir.rename(columns={
            'n_inscr': 'Número de Inscrição',
            'posicao': 'Posicao',
            'nome': 'Nome',
            'telefone': 'Telefone',
            'email': 'Email',
            'opcao': 'Opção',
            'formacao_academica': 'Formação',
            'grupo': 'Grupo',
            'cota': 'Cota'
        }, inplace=True)
        st.dataframe(df_exibir, hide_index=True)
    else:
        st.info("Nenhum usuário ainda se cadastrou nesse grupo.")

    # -----------------------------------------------------
    # 5. AUDITORIA: Verificar documento do usuário
    #    5.1. Verifica se usuário informado é do mesmo grupo.
    #    5.2. Exibe dados básicos e descriptografa o arquivo.
    # -----------------------------------------------------
    st.write("## Auditoria do Grupo")
    st.info("Verifique o documento de um usuário do seu grupo.")

    n_inscr_arquivo = st.text_input("Número de inscrição do usuário para auditoria")
    if st.button("Ver Documento"):
        user_record = usuarios_grupo[usuarios_grupo['n_inscr'] == n_inscr_arquivo]
        if user_record.empty:
            st.error("Usuário não encontrado ou não pertence ao seu grupo.")
        else:
            # Exibe dados principais do usuário
            row_user = user_record.iloc[0]
            st.write(f"**Nome**: {row_user['nome']}")
            st.write(f"**Telefone**: {row_user['telefone']}")
            st.write(f"**Email**: {row_user['email']}")

            # Tentar localizar o arquivo no diretório "documentos_auditoria"
            pasta_destino = "documentos_auditoria"
            if not os.path.exists(pasta_destino):
                st.error("Pasta de documentos não existe ou está vazia.")
                return

            # Encontrar qualquer arquivo que tenha n_inscr_arquivo no nome
            arquivos = [f for f in os.listdir(pasta_destino) if n_inscr_arquivo in f]
            if not arquivos:
                st.warning("Nenhum arquivo encontrado para esse usuário.")
            else:
                st.success(f"Arquivo(s) encontrado(s): {arquivos}")
                # Pegar o primeiro arquivo, ou exibir um selectbox, se preferir
                arquivo_escolhido = arquivos[0]
                caminho_arquivo = os.path.join(pasta_destino, arquivo_escolhido)

                # Descriptografar
                try:
                    chave = carregar_chave_criptografia()
                except ValueError as e:
                    st.error(f"Erro ao carregar chave de criptografia: {e}")
                    return

                with open(caminho_arquivo, "rb") as f:
                    conteudo_criptografado = f.read()

                try:
                    conteudo_decriptado = decriptar_arquivo(conteudo_criptografado, chave)
                except Exception as e:
                    st.error(f"Falha ao descriptografar o arquivo: {e}")
                    return

                # 1) Mostra a imagem na tela (se for PNG, JPG, etc.)
                st.image(
                    conteudo_decriptado, 
                    caption="Documento do usuário", 
                    use_container_width=True
                )

                # 2) Oferecer para baixar
                nome_original = arquivo_escolhido.replace(".enc", "")
                st.download_button(
                    label="Baixar Arquivo Descriptografado",
                    data=conteudo_decriptado,
                    file_name=nome_original
                )
                

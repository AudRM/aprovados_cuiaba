# controller/estatisticas_grupo_coordenador.py

import os
import streamlit as st
import pandas as pd
from mensageria import Mensageria
from database import TabelaUsuario, TabelaDocumentos, retornarAprovados, TabelaGrupos, TabelaMensagens
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
    df_aprovados = retornarAprovados(db)
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

            # Informa ao usuário que está carregando:
            with st.spinner("Carregando documento. Por favor, aguarde..."):
                documento = db.retornarValor(TabelaDocumentos, {'n_inscr': n_inscr_arquivo})

            if documento:
                documento = documento[0]

                # Exibir o documento como imagem
                try:
                    st.image(documento['conteudo'], caption=documento['nome_arquivo'], use_container_width=True)
                except Exception as e:
                    st.error(f"Erro ao exibir o documento: {e}")

                # Botão para baixar o documento
                st.download_button(
                    label="Baixar Documento",
                    data=documento['conteudo'],
                    file_name=documento['nome_arquivo']
                )
            else:
                st.error("Nenhum documento encontrado para este usuário.")
                    

import streamlit as st
from database import TabelaMensagens, TabelaUsuario, TabelaGrupos
from datetime import datetime



def criar_mensagem(db, usuario_logado):
    """
    Mostra a UI (form) para criar mensagem e também exibe as mensagens existentes.
    Usa a classe Mensageria para a lógica de CRUD.
    """
    st.subheader("Criar Mensagem para Aprovados")

    # Instancia a classe Mensageria com o db
    mensageria = Mensageria(db)

    with st.form("form_criar_mensagem"):
        titulo = st.text_input("Título da Mensagem")
        conteudo = st.text_area("Conteúdo da Mensagem", height=150)
        posicao_min = st.number_input("Posição mínima", min_value=1, value=1)
        posicao_max = st.number_input("Posição máxima", min_value=1, value=1000)

        # Seleção múltipla de cotas
        cotas_possiveis = ["AC", "Racial", "PCD"]
        cotas_escolhidas = st.multiselect(
            "Escolha a(s) cota(s)", 
            options=cotas_possiveis, 
            default=["AC"]
        )

        # Seleção múltipla de grupos
        df_grupos = db.retornarTabela(TabelaGrupos)
        df_grupos = df_grupos[df_grupos['grupo']!='TI_RAIZ']    # Ocultando o TI_RAIZ
        lista_grupos = sorted(df_grupos["grupo"].unique().tolist())

        # Mesmo se for coordenador, deixamos escolher todos
        grupos_escolhidos = st.multiselect(
            "Escolha o(s) grupo(s) para a mensagem", 
            options=lista_grupos, 
            default=[usuario_logado.grupo] if usuario_logado.role == "coordenador" else lista_grupos
        )

        enviar_btn = st.form_submit_button("Enviar Mensagem")

    # Ao clicar em Enviar, chamamos a classe Mensageria
    if enviar_btn:
        if not titulo.strip() or not conteudo.strip():
            st.error("Preencha título e conteúdo da mensagem.")
            return
        if not grupos_escolhidos:
            st.error("Selecione ao menos um grupo.")
            return
        if not cotas_escolhidas:
            st.error("Selecione ao menos uma cota.")
            return

        mensageria.criar_mensagem(
            titulo=titulo,
            conteudo=conteudo,
            grupos=grupos_escolhidos,
            cotas=cotas_escolhidas,
            posicao_min=posicao_min,
            posicao_max=posicao_max,
            autor=f"{usuario_logado.nome} (n_inscr: {usuario_logado.n_inscr})"
        )

        st.success("Mensagem(ens) criada(s) com sucesso!")

    # -------------------------------------------------
    # Exibir mensagens existentes (e permitir deletar)
    # -------------------------------------------------
    st.subheader("Mensagens Existentes")

    df_msgs = mensageria.listar_mensagens()
    if df_msgs.empty:
        st.info("Nenhuma mensagem cadastrada.")
    else:
        for idx, row in df_msgs.iterrows():
            with st.expander(
                f"{row['titulo']} (Grupo: {row['grupo']}, "
                f"Cota: {row['cota']}, "
                f"Posições: {row['posicao_min']} - {row['posicao_max']})"
                f" - Criada em {row['data_criacao']}"
            ):
                st.write(row["conteudo"])
                st.write(f"Autor: {row['autor']}")
                if st.button("Deletar mensagem", key=f"delete_msg_{row['id_mensagem']}"):
                    ok = mensageria.deletar_mensagem(row['id_mensagem'])
                    if ok:
                        st.success("Mensagem deletada com sucesso!")
                        st.rerun()
                    else:
                        st.error("Falha ao deletar ou mensagem não encontrada.")
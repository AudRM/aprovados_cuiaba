# controller/estatisticas.py

import streamlit as st
import pandas as pd
from grupos import Grupo
from database import TabelaGrupos, retornarAprovados, retornarListaUsuariosNaFrente, TabelaMensagens
from utils import is_valid_link
from mensageria import Mensageria

def apresentar_dados_gerais_usuario(usuario, db):
    """ Função para apresentar os dados normais do usuário """
    st.subheader("Dados Gerais")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label='Grupo', value=usuario.grupo)
    with col2:
        st.metric(label='Posição', value=usuario.posicao)
    with col3:
        st.metric(label='Perfil', value=usuario.role)


def apresentar_dados_decisoes(usuario, db):
    """ Função para apresentar os metrics com as informações sobre pessoas à frente"""
    st.subheader("Estatísticas do Grupo")
    grupo = Grupo(grupo=usuario.grupo, db=db)

    usuarios_frente = retornarListaUsuariosNaFrente(db, usuario.grupo, usuario.posicao, usuario.cota)
    
    aprovados_na_frente = retornarAprovados(db)
    aprovados_na_frente = aprovados_na_frente[
        (aprovados_na_frente['grupo'] == usuario.grupo) & 
        (aprovados_na_frente['posicao'] < usuario.posicao) &
        (aprovados_na_frente['cota'] == usuario.cota)
    ]
    total_aprovados_grupo = len(aprovados_na_frente)
    total_usuarios_frente = len(usuarios_frente)

    if total_aprovados_grupo > 0:
        percentual_frente = (total_usuarios_frente / total_aprovados_grupo) * 100
    else:
        percentual_frente = 0

    if total_usuarios_frente > 0:
        assumir = usuarios_frente[usuarios_frente['opcao'] == "Vai assumir"]
        indecisos = usuarios_frente[usuarios_frente['opcao'] == "Indeciso"]
        nao_assumir = usuarios_frente[usuarios_frente['opcao'] == "Não vai assumir"]

        # Exemplo: últimas atualizações no último dia
        ultimas_atualizacoes = usuarios_frente[
            usuarios_frente['data_ultima_modificacao'] >= pd.Timestamp.now() - pd.Timedelta(days=1)
        ]

        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="Usuários que irão assumir na minha frente", value=len(assumir))
            st.metric(label="Atualizações no último dia", value=len(ultimas_atualizacoes))

        with col2:
            st.metric(label="Usuários indecisos na minha frente", value=len(indecisos))
            st.metric(label="Usuários que não vão assumir na minha frente", value=len(nao_assumir))

        st.metric(
            label="Percentual de usuários já cadastrados",
            value=f"{percentual_frente:.2f}%"
        )

    elif total_aprovados_grupo == 0:
        st.text("Parabéns! Não há NENHUM candidato na sua frente em relação à sua cota/grupo! Só aguarde e a nomeação chegará!")
        
    else:
        st.text('Nenhum candidato à sua frente foi cadastrado. Aguarde.')
        st.metric(label="Percentual de usuários na minha frente", value=f"{percentual_frente:.2f}%")


def mostrar_link(usuario, db):
    """ Serve para mostrar o link do grupo ao usuário """
    usuarios = retornarListaUsuariosNaFrente(db, usuario.grupo, usuario.posicao, usuario.cota)
    grupo = Grupo(grupo=usuario.grupo, db=db)
    # Retirar usuários na frente que não vã assumir OU que não tenham se cadastrado ainda
    if not usuarios.empty:
        try:
            nao_vao_assumir = usuarios[usuarios['opcao']=="Não vai assumir"]['n_inscr'].unique()
        except:
            nao_vao_assumir = ['aaaaa', 'bbbbb']
    else:
        nao_vao_assumir = ['aaaaa', 'bbbbb']

    total_aprov = retornarAprovados(db)
    total_aprov = total_aprov[
            (total_aprov['grupo']==usuario.grupo)&
            (total_aprov['cota']==usuario.cota)&
            (total_aprov['posicao']<usuario.posicao)
            ]
    total_aprov = total_aprov[~total_aprov['n_inscr'].isin(nao_vao_assumir)]

    # Achar limite de CR para o grupo/cota
    tabela_grupo = db.retornarTabela(TabelaGrupos)
    tamanho_CR = tabela_grupo[(tabela_grupo['cota']==usuario.cota) & (tabela_grupo['grupo']==usuario.grupo)]['qtde_vagas'].values

    if total_aprov.shape[0] < tamanho_CR:  # Se tiver menos usuários à frente que vagas
        mensagem_grupo = grupo.mostrarMensagens()
        link_grupo = grupo.mostrarLink()

        if link_grupo['sucesso']:

            # Validar link de grupo
            if is_valid_link(link_grupo['resultado']):
                st.markdown(f"[Link do Grupo]({link_grupo['resultado']})", unsafe_allow_html=True)
            else:
                st.text('Link do grupo ainda não disponível.')
        else:
            st.error("Erro ao carregar link")
    
    else:
        st.write("### Mensagem do Grupo")
        st.text("Infelizmente ainda não chegou a sua vez para ser inserido no Grupo do CR de Cuiabá. Mas calma! Aguarde os outros aprovados confirmarem que não vão assumir ou aumentar a quantidade de vagas!")
        

def exibir_mensagens_usuario(usuario, db):
    """
    Mostra as mensagens destinadas ao usuário, e abre um 'pop-up'/expander
    para a mais recente que ele ainda não viu nesta sessão.
    """
    
    # (b) Histórico de mensagens
    st.write("### Histórico de Mensagens")

    # Obter todas as mensagens
    mensageria = Mensageria(db)
    df_mensagens = mensageria.listar_mensagens()
    
    if df_mensagens.empty:
        st.success("Nenhuma mensagem criada.")
        return 
    
    # Filtro para o grupo, cota, faixa de posição
    mask = (
        (df_mensagens["grupo"] == usuario.grupo) &
        (df_mensagens["cota"] == usuario.cota) &
        (df_mensagens["posicao_min"] <= usuario.posicao) &
        (df_mensagens["posicao_max"] >= usuario.posicao)
    )
    mensagens_pertinentes = df_mensagens[mask].sort_values("data_criacao", ascending=False)
    if mensagens_pertinentes.empty:
        st.success("Nenhuma mensagem criada para o usuário.")
    else:
        for i, row in mensagens_pertinentes.iterrows():
            with st.expander(f"{row['titulo']} (enviada em {row['data_criacao']})", expanded=False):
                st.write(row["conteudo"])


def home(usuario, db):
    """ Função para mostrar tudo do home a uma """
    apresentar_dados_gerais_usuario(usuario, db)
    exibir_mensagens_usuario(usuario, db)
    mostrar_link(usuario, db)
    apresentar_dados_decisoes(usuario, db)
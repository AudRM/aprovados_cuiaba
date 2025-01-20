# controller/estatisticas.py

import streamlit as st
import pandas as pd
from grupos import Grupo
from database import TabelaAprovados, TabelaGrupos, TabelaUsuario

def verificar_estatisticas(conta, db):
    st.subheader("Dados Gerais")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label='Grupo', value=conta.grupo)
    with col2:
        st.metric(label='Posição', value=conta.posicao)
    with col3:
        st.metric(label='Perfil', value=conta.role)

    st.subheader("Estatísticas do Grupo")
    grupo = Grupo(grupo=conta.grupo, db=db)

    usuarios_frente = db.retornarListaUsuariosNaFrente(conta.grupo, conta.posicao, conta.cota)
    
    aprovados_na_frente = db.retornarTabela(TabelaAprovados)
    aprovados_na_frente = aprovados_na_frente[
        (aprovados_na_frente['grupo'] == conta.grupo) & 
        (aprovados_na_frente['posicao'] < conta.posicao) &
        (aprovados_na_frente['cota'] == conta.cota)
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
        st.text("Porra, mané, tu é brabão mesmo, hein? Parabéns.")
        
    else:
        st.text('Nenhum candidato à sua frente foi cadastrado. Aguarde.')
        st.metric(label="Percentual de usuários na minha frente", value=f"{percentual_frente:.2f}%")


    usuarios = db.retornarListaUsuariosNaFrente(conta.grupo, conta.posicao, conta.cota)
    

    
    # Retirar usuários na frente que não vã assumir OU que não tenham se cadastrado ainda
    
    if not usuarios.empty:
        try:
            nao_vao_assumir = usuarios[usuarios['opcao']=="Não vai assumir"]['n_inscr'].unique()
        except:
            nao_vao_assumir = ['aaaaa', 'bbbbb']
    else:
        nao_vao_assumir = ['aaaaa', 'bbbbb']

    total_aprov = db.retornarTabela(TabelaAprovados)
    total_aprov = total_aprov[
            (total_aprov['grupo']==conta.grupo)&
            (total_aprov['cota']==conta.cota)&
            (total_aprov['posicao']<conta.posicao)
            ]
    total_aprov = total_aprov[~total_aprov['n_inscr'].isin(nao_vao_assumir)]


    # Achar limite de CR para o grupo/cota
    tabela_grupo = db.retornarTabela(TabelaGrupos)
    tamanho_CR = tabela_grupo[(tabela_grupo['cota']==conta.cota) & (tabela_grupo['grupo']==conta.grupo)]['qtde_vagas'].values

    

    if total_aprov.size < tamanho_CR:  # Se tiver menos usuários à frente que vagas
    
        mensagem_grupo = grupo.mostrarMensagens()
        link_grupo = grupo.mostrarLink()

        st.write("### Mensagem do Grupo")
        if mensagem_grupo['sucesso']:
            st.text(mensagem_grupo['resultado'])
        else:
            st.error("Erro ao carregar mensagem")

        if link_grupo['sucesso']:
            st.text_input("Link do Grupo", link_grupo['resultado'], disabled=True)
        else:
            st.error("Erro ao carregar link")
    
    else:
        st.write("### Mensagem do Grupo")
        st.text("Infelizmente ainda não chegou a sua vez para ser inserido no Grupo do CR de Cuiabá. Mas calma! Aguarde os outros aprovados confirmarem que não vão assumir ou aumentar a quantidade de vagas!")
        


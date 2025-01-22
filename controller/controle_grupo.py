# controller/controle_grupo.py

import streamlit as st
from database import TabelaGrupos

def controle_de_grupo(conta, db):
    """
    Permite que o coordenador atualize a qtde_vagas e link 
    do seu grupo, para cada cota.
    """
    st.title("Controle de Grupo")
    st.write(f"Bem-vindo, {conta.nome}! Grupo: {conta.grupo}")

    st.subheader("Atualizar Vagas e Link por Cota")

    # 1. Selecionar a cota
    opcoes_cota = ["AC", "Racial", "PCD"]
    cota_escolhida = st.selectbox("Escolha a cota", opcoes_cota)

    # 2. Buscar registro na TabelaGrupos (grupo = conta.grupo, cota = cota_escolhida)
    registro = db.retornarValor(
        TabelaGrupos,
        filter_dict={"grupo": conta.grupo, "cota": cota_escolhida}
    )

    if registro:
        # Se já existe, obtemos qtde_vagas/link atuais
        registro_atual = registro[0]
        vagas_atuais = registro_atual['qtde_vagas']
        link_atual = registro_atual['link']
    else:
        # Se não existir, assumimos algo padrão
        vagas_atuais = 0
        link_atual = ""

    # 3. Inputs para edição
    qtde_vagas = st.number_input("Quantidade de Vagas", value=vagas_atuais, min_value=0)
    link_grupo = st.text_input("Link do grupo de WhatsApp", value=link_atual)

    # 4. Botão para atualizar
    if st.button("Atualizar"):
        # Verifica se o registro já existe
        if registro:
            # Atualizamos
            db.atualizarTabela(
                TabelaGrupos,
                filter_dict={"grupo": conta.grupo, "cota": cota_escolhida},
                update_dict={"qtde_vagas": qtde_vagas, "link": link_grupo}
            )
            st.success("Dados atualizados com sucesso!")
        else:
            # Inserimos
            dados_novos = {
                "grupo": conta.grupo,
                "cota": cota_escolhida,
                "qtde_vagas": qtde_vagas,
                "link": link_grupo
            }
            db.inserirDados(TabelaGrupos, dados_novos)
            st.success("Dados inseridos com sucesso!")

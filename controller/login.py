"""

Aquivo para manter funções de controlador e visualizador de login

"""

# controller/login.py

import streamlit as st
import os
import datetime
from database import TabelaAprovados
from utils import carregar_chave_criptografia, encriptar_arquivo

def criar_conta(db, conta_manager):
    st.subheader("Criar Conta")
    with st.form("Criar Conta"):
        n_inscr = st.text_input("Número de Inscrição")
        senha = st.text_input("Senha", type="password")
        email = st.text_input("E-mail [Opcional]")
        telefone = st.text_input("Telefone [Opcional]")
        formacao_academica = st.text_input("Formação Acadêmica [Opcional]")
        opcao_selecionada = st.selectbox("Opção", ["Não vou assumir", "Vou assumir", "Estou indeciso"])
        documento = st.file_uploader("Envie uma imagem do documento", type=["png", "jpg", "jpeg"])

        # Mapeia a opção
        opcao = {
            "Não vou assumir": "Não vai assumir",
            "Vou assumir": "Vai assumir",
            "Estou indeciso": "Indeciso"
        }[opcao_selecionada]

        submit = st.form_submit_button("Criar")

        if submit:
            # 1. Verifica se a inscrição existe no TabelaAprovados
            dados_candidato = db.retornarValor(TabelaAprovados, filter_dict={'n_inscr': n_inscr})
            if not dados_candidato:
                st.error("Número de inscrição não encontrado no banco.")
                return

            # 2. Verifica se foi enviado algum documento
            if not documento:
                st.error("Por favor, envie uma imagem do documento.")
                return

            # 3. Carrega a chave de criptografia das variáveis de ambiente
            try:
                chave = carregar_chave_criptografia()
            except ValueError as e:
                st.error(str(e))
                return

            # 4. Criptografa o arquivo
            conteudo_arquivo = documento.read()
            conteudo_criptografado = encriptar_arquivo(conteudo_arquivo, chave)

            # 5. Salva o arquivo criptografado
            pasta_destino = "documentos_auditoria"
            if not os.path.exists(pasta_destino):
                os.makedirs(pasta_destino, exist_ok=True)

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            extensao = documento.name.split('.')[-1]
            nome_arquivo = f"{n_inscr}_{timestamp}.{extensao}.enc"
            caminho_arquivo = os.path.join(pasta_destino, nome_arquivo)

            with open(caminho_arquivo, "wb") as f:
                f.write(conteudo_criptografado)

            # 6. Cria a conta no banco (senha hasheada, etc.)
            resultado = conta_manager.criarConta(
                n_inscr=n_inscr, 
                senha=senha,
                email=email,
                telefone=telefone,
                formacao_academica=formacao_academica,
                opcao=opcao
            )

            if resultado['sucesso']:
                st.success("Cadastro criado com sucesso!")
            else:
                st.error("Erro ao salvar os dados no banco.")

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


def pagina_login(db, conta_manager):
    st.title("Bem-vindo ao Sistema de Gestão de Candidatos")
    st.text("Este sistema é gerido pelos próprios candidatos, de forma a facilitar o contato entre os aprovados.")

    if 'logado' not in st.session_state:
        st.session_state['logado'] = False

    opcao = st.radio("Escolha uma opção:", ["Login", "Criar Conta"])

    if opcao == "Criar Conta":
        criar_conta(db, conta_manager)
    elif opcao == "Login":
        login(db, conta_manager)
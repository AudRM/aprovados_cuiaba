import streamlit as st
from database import Database, TabelaAprovados, TabelaGrupos, TabelaUsuario
from contas import Conta
from grupos import Grupo
from usuarios import Usuario
import pandas as pd 

# Inicialização do banco de dados e objetos principais
db = Database()
conta_manager = Conta(db=db)


import os
import datetime

def criar_conta():
    st.subheader("Criar Conta")
    with st.form("Criar Conta"):
        n_inscr = st.text_input("Número de Inscrição")
        senha = st.text_input("Senha", type="password")
        email = st.text_input("E-mail [Opcional]")
        telefone = st.text_input("Telefone [Opcional]")
        formacao_academica = st.text_input("Formação Acadêmica [Opcional]")
        opcao_selecionada = st.selectbox("Opção", ["Não vou assumir", "Vou assumir", "Estou indeciso"])
        documento = st.file_uploader("Envie uma imagem do documento", type=["png", "jpg", "jpeg"])

        # Mapear opção selecionada para o valor a ser inserido no banco de dados
        opcao = {
            "Não vou assumir": "Não vai assumir",
            "Vou assumir": "Vai assumir",
            "Estou indeciso": "Indeciso"
        }[opcao_selecionada]

        submit = st.form_submit_button("Criar")

        if submit:
            # Pega o nome do candidato no banco pela inscrição:
            dados_candidato = db.retornarValor(TabelaAprovados, filter_dict={'n_inscr': n_inscr})
            if not dados_candidato:
                st.error("Número de inscrição não encontrado no banco.")
                return

            if documento:
                # Salvar o documento para auditoria
                pasta_destino = "documentos_auditoria"
                if not os.path.exists(pasta_destino):
                    os.makedirs(pasta_destino)

                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                extensao = documento.name.split('.')[-1]
                nome_arquivo = f"{n_inscr}_{timestamp}.{extensao}"
                caminho_arquivo = os.path.join(pasta_destino, nome_arquivo)

                with open(caminho_arquivo, "wb") as f:
                    f.write(documento.getbuffer())

                # Inserir dados no banco
                resultado = conta_manager.criarConta(n_inscr=n_inscr, senha=senha, email=email, opcao=opcao, telefone=telefone, formacao_academica=formacao_academica)

                if resultado['sucesso']:
                    st.query_params = ''  # Limpa mensagens anteriores
                    st.success("Cadastro criado com sucesso")
                else:
                    st.error("Erro ao salvar os dados no banco.")
            else:
                st.error("Por favor, envie uma imagem do documento.")


            
def login():
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
                st.query_params = ''  # Limpa mensagens anteriores
                st.success("Acesso realizado com sucesso!")
                st.rerun()
            else:
                st.error(resultado['resultado'])

def pagina_login():
    st.title("Bem-vindo ao Sistema de Gestão de Candidatos")

    if 'logado' not in st.session_state:
        st.session_state['logado'] = False

    opcao = st.radio("Escolha uma opção:", ["Login", "Criar Conta"])

    if opcao == "Criar Conta":
        criar_conta()
    elif opcao == "Login":
        login()

def pagina_principal():
    st.title("Painel do Usuário")

    conta = st.session_state.get('conta')

    if conta:
        lista_menu = ["Ver Estatísticas", "Gerenciar Dados", "Sair"]
        if conta.role == 'superuser':
            lista_menu.insert(2, 'Administrar Banco de Dados')

        menu = st.sidebar.selectbox("Menu", lista_menu)
        if menu == "Ver Estatísticas":
            verificar_estatisticas(conta)

        elif menu == "Gerenciar Dados":
            gerenciar_dados_usuario(conta)

        elif menu == "Sair":
            st.session_state['logado'] = False
            st.session_state['conta'] = None
            st.query_params = ''  # Limpa mensagens anteriores
            st.rerun()

        elif menu == 'Administrar Banco de Dados':
            administrar_web_app()
    
    
    else:
        st.warning("Erro: Conta não encontrada. Faça login novamente.")
        st.session_state['logado'] = False
        st.rerun()



import streamlit as st
from database import Database, TabelaUsuario
import pandas as pd
import os
import datetime

def administrar_web_app():
    st.subheader('Painel de Administração - Superusuário')

    db = Database()

    # Exibir todos os usuários cadastrados
    st.write("### Usuários Registrados")
    usuarios = db.retornarTabela(TabelaUsuario)

    if usuarios.empty:
        st.warning("Nenhum usuário registrado.")
        return

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

    # Resetar senha (deletar conta do usuário)
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
        arquivos = [f for f in os.listdir(pasta_destino) if n_inscr_arquivo in f]
        if arquivos:
            st.success(f"Arquivo encontrado: {arquivos[0]}")
            caminho_arquivo = os.path.join(pasta_destino, arquivos[0])
            with open(caminho_arquivo, "rb") as f:
                st.download_button(label="Baixar Arquivo", data=f, file_name=arquivos[0])
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
            st.download_button(label="Baixar Arquivo Exportado", data=f, file_name=os.path.basename(caminho_arquivo))

    st.subheader('Administração de Dados')

    documento = st.file_uploader("Envie a lista de aprovados (CSV)", type=["csv"])

    if documento is not None:
        # Lê o CSV como DataFrame
        df = pd.read_csv(documento)
        
        # Contador para as linhas adicionadas
        linhas_adicionadas = 0

        # Itera sobre cada linha do DataFrame
        for _, row in df.iterrows():
            # Exemplo: assumimos que existe uma coluna 'n_inscr' (número de inscrição)
            # e uma coluna 'nome' no CSV. Ajuste conforme seu schema real.
            numero_inscricao = row['n_inscr']
            nome = row['nome']
            posicao = row['posicao']
            grupo = row['grupo']

            # Verifica se já existe no banco
            registro_existente = db.retornarValor(
                TabelaAprovados,
                filter_dict={'n_inscr': numero_inscricao}
            )

            if not registro_existente:
                # Se não existir, insere
                dados_para_inserir = {
                    'n_inscr': numero_inscricao,
                    'nome': nome
                    # Coloque aqui as outras colunas, se necessário
                }
                db.inserirValor(TabelaAprovados, dados_para_inserir)
                linhas_adicionadas += 1

        st.success(f"Processo concluído! {linhas_adicionadas} linha(s) adicionada(s) ao banco.")


# def administrar_web_app():
#     st.subheader('Administração de Dados')

#     documento = st.file_uploader("Envie a lista de aprovados (CSV)", type=["csv"])

#     if documento is not None:
#         # Lê o CSV como DataFrame
#         df = pd.read_csv(documento)
        
#         # Contador para as linhas adicionadas
#         linhas_adicionadas = 0

#         # Itera sobre cada linha do DataFrame
#         for _, row in df.iterrows():
#             # Exemplo: assumimos que existe uma coluna 'n_inscr' (número de inscrição)
#             # e uma coluna 'nome' no CSV. Ajuste conforme seu schema real.
#             numero_inscricao = row['n_inscr']
#             nome = row['nome']
#             posicao = row['posicao']
#             grupo = row['grupo']

#             # Verifica se já existe no banco
#             registro_existente = db.retornarValor(
#                 TabelaAprovados,
#                 filter_dict={'n_inscr': numero_inscricao}
#             )

#             if not registro_existente:
#                 # Se não existir, insere
#                 dados_para_inserir = {
#                     'n_inscr': numero_inscricao,
#                     'nome': nome
#                     # Coloque aqui as outras colunas, se necessário
#                 }
#                 db.inserirValor(TabelaAprovados, dados_para_inserir)
#                 linhas_adicionadas += 1

#         st.success(f"Processo concluído! {linhas_adicionadas} linha(s) adicionada(s) ao banco.")

#     st.subheader('Administração de Usuários')

#     usuarios = db.retornarTabela(TabelaUsuario)

#     st.data_frame()

def verificar_estatisticas(conta):

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

    # Dados principais
    usuarios_frente = db.retornarListaUsuariosNaFrente(conta.grupo, conta.posicao)
    aprovados_na_frente = db.retornarTabela(TabelaAprovados)
    aprovados_na_frente = aprovados_na_frente[(aprovados_na_frente['grupo']==conta.grupo) & (aprovados_na_frente['posicao'] < conta.posicao)]
    total_aprovados_grupo = len(aprovados_na_frente)
    
    total_usuarios_frente = len(usuarios_frente)


    # Métricas específicas
    if total_usuarios_frente > 0:
        assumir = usuarios_frente[usuarios_frente['opcao'] == "Vai assumir"]
        indecisos = usuarios_frente[usuarios_frente['opcao'] == "Indeciso"]
        nao_assumir = usuarios_frente[usuarios_frente['opcao'] == "Não vai assumir"]

        ultimas_atualizacoes = usuarios_frente[usuarios_frente['data_ultima_modificacao'] >= pd.Timestamp.now() - pd.Timedelta(days=1)]

    
        percentual_frente = (total_usuarios_frente / total_aprovados_grupo) * 100 if total_aprovados_grupo > 0 else 0

        # Divisão em colunas para melhorar aparência
        col1, col2 = st.columns(2)

        with col1:
            st.metric(label="Usuários que irão assumir na minha frente", value=len(assumir))
            st.metric(label="Atualizações no último dia", value=len(ultimas_atualizacoes))
        
        with col2:
            st.metric(label="Usuários indecisos na minha frente", value=len(indecisos))
            
            st.metric(label="Usuários que não vão assumir na minha frente", value=len(nao_assumir))

        st.metric(label="Percentual de usuários na minha frente já cadastrados", value=f"{percentual_frente:.2f}%")
    
    elif total_aprovados_grupo == 0:
        st.text("Porra, mané, tu é brabão mesmo, hein? Parabéns.")

    else:
        # Divisão em colunas para melhorar aparência
        st.text('Nenhum candidato à sua frente foi cadastrado. Aguarde.')

        st.metric(label="Percentual de usuários na minha frente", value=f"{percentual_frente:.2f}%") 

    # Mensagem e link do grupo
    mensagem_grupo = grupo.mostrarMensagens()
    link_grupo = grupo.mostrarLink()

    st.write("### Mensagem do Grupo")
    st.text(mensagem_grupo['resultado'] if mensagem_grupo['sucesso'] else "Erro ao carregar mensagem")

    st.text_input("Link do Grupo", link_grupo['resultado'] if link_grupo['sucesso'] else "Erro ao carregar link", disabled=True)


def gerenciar_dados_usuario(conta):
    st.subheader("Gerenciamento de Dados do Usuário")
    with st.form("Atualizar Dados"):
        novo_email = st.text_input("Novo E-mail", value=conta.email)
        novo_telefone = st.text_input("Novo Telefone", value=conta.telefone)
        nova_opcao_selecionada = st.selectbox("Nova Opção", ["Não vou assumir", "Vou assumir", "Estou indeciso"], index=["Não vai assumir", "Vai assumir", "Indeciso"].index(conta.opcao))

        # Mapear nova opção selecionada para o valor a ser inserido no banco de dados
        nova_opcao = {
            "Não vou assumir": "Não vai assumir",
            "Vou assumir": "Vai assumir",
            "Estou indeciso": "Indeciso"
        }[nova_opcao_selecionada]

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
                st.query_params = ''  # Limpa mensagens anteriores
            else:
                st.error(resultado['resultado'])

# Navegação entre páginas
if 'logado' not in st.session_state or not st.session_state['logado']:
    pagina_login()
else:
    pagina_principal()
# controller/pagina.py

import streamlit as st

# Importa as funções que já criamos para cada funcionalidade
from controller.login import login, criar_conta
from controller.estatisticas import verificar_estatisticas
from controller.dados_usuarios import gerenciar_dados_usuario
from controller.adm import administrar_web_app
from controller.estatisticas_grupo_coordenador import estatisticas_de_grupo_coordenador
from controller.controle_grupo import controle_de_grupo
from data_p_config.textos import TEXTO_PROPOSITO_WEBAPP

class Pagina:
    """
    Classe que concentra a navegação da aplicação.
    - Login ou criação de conta.
    - Verifica o tipo (role) do usuário ao logar.
    - Se logado:
        - usuarios básicos: ver estatísticas do usuário
        - coordenadores/superuser: (futuro) ver estatísticas de grupo
        - superuser: ver painel de administração
    """
    def __init__(self, db, conta_manager):
        self.db = db
        self.conta_manager = conta_manager

    def exibir(self):
        """
        Função principal. Decide se exibe a tela de login ou
        a página principal, conforme o estado de sessão.
        """
        if 'logado' not in st.session_state or not st.session_state['logado']:
            self._pagina_login()
        else:
            self._pagina_principal()

    def _pagina_login(self):
        """
        Exibe a tela de login ou de criar conta.
        """
        st.title("Bem-vindo ao Sistema de Gestão de Aprovados ISS Cuiabá")
        st.text(TEXTO_PROPOSITO_WEBAPP)
        opcao = st.radio("Escolha uma opção:", ["Login", "Criar Conta"])

        if opcao == "Criar Conta":
            criar_conta(self.db, self.conta_manager)
        elif opcao == "Login":
            login(self.db, self.conta_manager)

    def _pagina_principal(self):
        """
        Exibe o painel principal, dependendo do tipo de usuário.
        """
        conta = st.session_state.get('conta')
        if not conta:
            # Se algo falhou e não tem 'conta', retorna ao login
            st.warning("Erro: Conta não encontrada. Faça login novamente.")
            st.session_state['logado'] = False
            st.experimental_rerun()
            return

        # Mostra menu lateral ou superior, dependendo da sua preferência
        if conta.role == 'superuser':
            opcoes_menu = [
                "Ver Estatísticas (Usuário)",
                "Estatísticas de Grupo (Coordenador)",
                "Controle de Grupo",       # NOVA OPÇÃO
                "Administração (Superuser)",
                "Gerenciar Dados de Usuário",
                "Sair"
            ]
        elif conta.role == 'coordenador':
            opcoes_menu = [
                "Ver Estatísticas (Usuário)",
                "Estatísticas de Grupo (Coordenador)",
                "Controle de Grupo",       # NOVA OPÇÃO
                "Gerenciar Dados de Usuário",
                "Sair"
            ]
        else:
            # role == 'usuario'
            opcoes_menu = ["Ver Estatísticas (Usuário)",
                           "Gerenciar Dados de Usuário",
                           "Sair"]

        escolha = st.sidebar.selectbox("Menu", opcoes_menu)

        # Módulo para estatísticas do usuário (já implementado antes)
        if escolha == "Ver Estatísticas (Usuário)":
            verificar_estatisticas(conta, self.db)

        # Estatísticas de grupo (coordenador / superuser)
        elif escolha == "Estatísticas de Grupo (Coordenador)":
            if conta.role in ['coordenador', 'superuser']:
                estatisticas_de_grupo_coordenador(conta, self.db)
            else:
                st.error("Você não tem permissão para esta seção.")

        # Painel de administração (superuser)
        elif escolha == "Administração (Superuser)":
            if conta.role == 'superuser':
                administrar_web_app(self.db)
            else:
                st.error("Você não tem permissão para esta seção.")

        # Gerenciamento de dados do próprio usuário (mudar email, telefone, etc.)
        elif escolha == "Gerenciar Dados de Usuário":
            gerenciar_dados_usuario(conta, self.db)

        if escolha == "Controle de Grupo":
            if conta.role in ['coordenador', 'superuser']:
                from controller.controle_grupo import controle_de_grupo
                controle_de_grupo(conta, self.db)
            else:
                st.warning("Você não tem permissão para este recurso.")

        # Sair
        elif escolha == "Sair":
            st.session_state['logado'] = False
            st.session_state['conta'] = None
            st.rerun()

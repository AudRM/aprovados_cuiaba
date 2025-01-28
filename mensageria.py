"""

Classe de Mensageria, responsável por fazer a gestão das mensagens para os usuários.

"""

# mensageria.py

from database import TabelaMensagens, TabelaUsuario
from datetime import datetime
import requests
import streamlit as st

class Mensageria:
    """
    Responsável por criar, excluir e gerenciar o envio das mensagens 
    (incluso disparar via WhatsApp).
    """

    def __init__(self, db):
        """
        :param db: Instância de Database para operar o CRUD.
        """
        self.db = db

    def criar_mensagem(self, 
                       titulo: str, 
                       conteudo: str, 
                       grupos: list, 
                       cotas: list, 
                       posicao_min: int, 
                       posicao_max: int, 
                       autor: str):
        """
        Cria uma ou várias mensagens no banco, baseando-se em 
        múltiplos grupos e cotas. 
        Em seguida, envia via WhatsApp para cada usuário que se encaixe no critério.
        """
        # 1) Inserir no banco (uma mensagem para cada combinação grupo/cota)
        for grupo in grupos:
            for cota in cotas:
                nova_msg = {
                    "grupo": grupo,
                    "cota": cota,
                    "posicao_min": posicao_min,
                    "posicao_max": posicao_max,
                    "titulo": titulo,
                    "conteudo": conteudo,
                    "autor": autor
                }
                self.db.inserirDados(TabelaMensagens, nova_msg)

        # 2) Após criar, chamamos a lógica de envio via WhatsApp
        # self._enviar_para_whatsapp(grupos, cotas, posicao_min, posicao_max, conteudo)


    def listar_mensagens(self):
        """
        Retorna todas as mensagens existentes (DataFrame).
        """
        mensagens = self.db.retornarTabela(TabelaMensagens)
        
        if not mensagens.empty:
            return mensagens.sort_values("data_criacao", ascending=False)
        
        return mensagens


    def deletar_mensagem(self, id_mensagem: int) -> bool:
        """
        Exclui do banco a mensagem cujo ID for fornecido.
        Retorna True se conseguiu deletar, False caso não encontre.
        """
        with self.db.get_session() as session:
            msg_obj = session.query(TabelaMensagens).filter_by(id_mensagem=id_mensagem).first()
            if msg_obj:
                session.delete(msg_obj)
                session.commit()
                return True
            return False

    def _enviar_para_whatsapp(self, grupos: list, cotas: list, posicao_min: int, posicao_max: int, conteudo: str):
        """
        Localiza os usuários que se encaixam nos filtros e dispara a API de WhatsApp
        (ou gera links para envio). Ajuste conforme sua integração real.
        """

        # 1) Buscar usuários relevantes
        with self.db.get_session() as session:
            matched_users = (
                session.query(TabelaUsuario)
                .filter(TabelaUsuario.grupo.in_(grupos))
                .filter(TabelaUsuario.cota.in_(cotas))
                .filter(TabelaUsuario.posicao >= posicao_min)
                .filter(TabelaUsuario.posicao <= posicao_max)
                .all()
            )

        TWILIO_SID = st.secrets["TWILIO_SID"]
        TWILIO_TOKEN = st.secrets["TWILIO_TOKEN"]
        url_api = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_SID}/Messages.json"

        for u in matched_users:
            telefone_limpo = ...
            if telefone_limpo:
                data = {
                    "From": "whatsapp:+14155238886",  # Exemplo de número do sandbox
                    "Body": conteudo,
                    "To": f"whatsapp:+55{telefone_limpo}"
                }
                resp = requests.post(url_api, data=data, auth=(TWILIO_SID, TWILIO_TOKEN))
                if resp.status_code == 201:
                    print(f"Mensagem enviada para {u.nome}")
                else:
                    print(f"Falha ao enviar p/ {u.nome}: {resp.text}")
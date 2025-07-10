import streamlit as st
import json
import os
import pandas as pd
import numpy as np
from datetime import datetime
from itertools import product

#Config da página
st.set_page_config(
    page_title="Tickets Sismaterial",
    page_icon="images/logo_elco_ajustado.png",
    layout="wide"
)

st.logo(
    "images/logo_elco.png",
    link=None,
    icon_image=None
)

def carregar_usuarios():
    if os.path.exists("dados_cadastrais.json"):
        with open("dados_cadastrais.json", "r", encoding='utf-8') as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                return {}
    return {}

def salvar_usuarios(usuarios):
    with open("dados_cadastrais.json", "w", encoding='utf-8') as file:
        json.dump(usuarios, file, indent=4, ensure_ascii=False)

def cadastrar_usuario(email, nome, senha, usuarios):
    """Cadastra novo usuário usando e-mail como chave"""
    if email in usuarios:
        return False
    usuarios[email] = {
        "nome": nome,
        "senha": senha
    }
    salvar_usuarios(usuarios)
    return True

def autenticar_usuario(email, senha, usuarios):
    """Autentica usando e-mail e senha"""
    return email in usuarios and usuarios[email]["senha"] == senha

def pagina_principal():
    st.title("PORTAL DE TICKETS DO SISTEMA PDMS 🎫")

    st.markdown("---")
    st.markdown(f"Olá, **{st.session_state.get('username', 'usuário')}** 👋")
    st.markdown("Use este espaço para registrar problemas relacionados a sistemas ou dados.")

    with st.expander("➕ Enviar solicitação"):
        with st.form("formulario_ticket", clear_on_submit=True):
            st.subheader("Nova Solicitação de Suporte")

            titulo = st.text_input("Título do problema")
            tipo = st.selectbox("Tipo de problema", ["Sistema em si", "Dados do Sistema", "Customização do Sistema", "Portal de tickets"])
            prioridade = st.selectbox("Prioridade", ["Média", "Baixa", "Alta"])
            descricao = st.text_area("Descreva o problema", height=150)
            arquivos = st.file_uploader("Anexar arquivos (opcional)", type=["jpg", "jpeg", "png", "pdf"], accept_multiple_files=True)

            enviar = st.form_submit_button("📩 Enviar solicitação")

            if enviar:
                if not titulo or not descricao:
                    st.warning("Por favor, preencha o título e a descrição do problema.")
                else:
                    ticket = {
                        "usuario": st.session_state.get("username", "Anônimo"),
                        "email": st.session_state.get("email", ""),
                        "data": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "titulo": titulo,
                        "tipo": tipo,
                        "prioridade": prioridade,
                        "descricao": descricao,
                        "arquivos": [f.name for f in arquivos] if arquivos else []
                    }

                    # Salvar ticket em arquivo JSON
                    tickets = []
                    if os.path.exists("tickets.json"):
                        with open("tickets.json", "r", encoding="utf-8") as f:
                            try:
                                tickets = json.load(f)
                            except:
                                pass

                    tickets.append(ticket)
                    with open("tickets.json", "w", encoding="utf-8") as f:
                        json.dump(tickets, f, indent=4, ensure_ascii=False)

                    # Opcional: salvar arquivos
                    if arquivos:
                        pasta_uploads = "uploads"
                        os.makedirs(pasta_uploads, exist_ok=True)
                        for file in arquivos:
                            with open(os.path.join(pasta_uploads, file.name), "wb") as f:
                                f.write(file.read())

                    st.success("✅ Solicitação enviada com sucesso!")

    st.markdown("---")
    st.subheader("Solicitações Registradas")

    # Carrega os tickets
    tickets = []
    if os.path.exists("tickets.json"):
        with open("tickets.json", "r", encoding="utf-8") as f:
            try:
                tickets = json.load(f)
            except:
                st.error("Erro ao carregar tickets.")

    if not tickets:
        st.info("Nenhuma solicitação registrada ainda.")
    else:
        # Gera um número de ticket formatado
        for idx, t in enumerate(tickets):
            t["numero"] = str(idx + 1).zfill(4)
            if "status" not in t:
                t["status"] = "Aberto"  # Valor padrão caso não tenha status

        # Ordena por data decrescente
        tickets = sorted(tickets, key=lambda x: x["data"], reverse=True)

        df = pd.DataFrame([{
            "Ticket": t["numero"],
            "Título": t["titulo"],
            "Data": t["data"],
            "Status": t["status"]
        } for t in tickets])

        busca = st.text_input("🔍 Buscar título ou número do ticket:")
        if busca:
            df = df[df["Título"].str.contains(busca, case=False) | df["Ticket"].str.contains(busca)]

        # Mostrar a tabela
        st.dataframe(df, use_container_width=True)

        # Link para abrir detalhes
        st.markdown("### Visualizar andamento de um ticket")
        ticket_selecionado = st.selectbox("Escolha o número do ticket:", df["Ticket"].tolist())

        if st.button("Ver Ticket"):
            st.session_state["ticket_aberto"] = ticket_selecionado
            st.session_state["pagina_atual"] = "ticket_detalhe"
            st.rerun()

def pagina_ticket_detalhe():
    st.title("Detalhes do Ticket")

    numero = st.session_state.get("ticket_aberto")
    if not numero:
        st.warning("Nenhum ticket selecionado.")
        return

    # Carrega os tickets
    if not os.path.exists("tickets.json"):
        st.error("Arquivo de tickets não encontrado.")
        return

    with open("tickets.json", "r", encoding="utf-8") as f:
        try:
            tickets = json.load(f)
        except:
            st.error("Erro ao ler tickets.")
            return

    usuarios = carregar_usuarios()
    email_logado = st.session_state.get("email", "")
    perfil_logado = usuarios.get(email_logado, {}).get("perfil", "usuario")


    ticket = None
    for idx, t in enumerate(tickets):
        if str(idx + 1).zfill(4) == numero:
            ticket = t
            break

    if not ticket:
        st.warning("Ticket não encontrado.")
        return

    col_chat, col_info = st.columns([2, 1])  # Chat à esquerda, Info à direita

    # === COLUNA DA DIREITA - DADOS DO TICKET ===
    with col_info:
        st.markdown(f"**Número do Ticket:** `{numero}`")
        st.markdown(f"**Solicitante:** {ticket.get('usuario', 'Não informado')}")
        st.markdown(f"**E-mail:** {ticket.get('email', 'Não informado')}")
        st.markdown(f"**Título:** {ticket['titulo']}")
        st.markdown(f"**Tipo:** {ticket['tipo']}")
        st.markdown(f"**Prioridade:** {ticket['prioridade']}")
        status_atual = ticket.get("status", "Aberto")
        if perfil_logado == "suporte":
            novo_status = st.selectbox("Status:", ["Aberto", "Em Análise", "Aguardando Retorno", "Resolvido"], index=["Aberto", "Em Análise", "Aguardando Retorno", "Resolvido"].index(status_atual))
            if novo_status != status_atual:
                ticket["status"] = novo_status
                idx = int(numero) - 1
                tickets[idx] = ticket
                with open("tickets.json", "w", encoding="utf-8") as f:
                    json.dump(tickets, f, indent=4, ensure_ascii=False)
                st.success("✅ Status atualizado com sucesso!")
                st.rerun()
        else:
            st.markdown(f"**Status:** `{status_atual}`")
        st.markdown(f"**Data:** {ticket['data']}")
        st.markdown("**Descrição:**")
        st.info(ticket['descricao'])

        if ticket.get("arquivos"):
            st.markdown("**Arquivos Anexados:**")
            for nome_arquivo in ticket["arquivos"]:
                caminho_arquivo = os.path.join("uploads", nome_arquivo)
                if os.path.exists(caminho_arquivo):
                    with open(caminho_arquivo, "rb") as f:
                        st.download_button(
                            label=f"📥 {nome_arquivo}",
                            data=f.read(),
                            file_name=nome_arquivo,
                            mime="application/octet-stream"
                        )
                else:
                    st.warning(f"Arquivo '{nome_arquivo}' não encontrado.")

    # === COLUNA DA ESQUERDA - CHAT ===
    with col_chat:
        st.subheader("💬 Chat da Solicitação")

        # Caixa de envio primeiro
        nova_msg = st.text_area("Digite sua mensagem", key="mensagem_chat")

        if st.button("✉️ Enviar Mensagem"):
            if nova_msg.strip():
                if "mensagens" not in ticket:
                    ticket["mensagens"] = []

                ticket["mensagens"].insert(0, {  # insert(0, ...) para manter ordem reversa (mais recente em cima)
                    "usuario": st.session_state.get("username", "Anônimo"),
                    "data": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "mensagem": nova_msg.strip()
                })

                # Atualiza JSON
                idx = int(numero) - 1
                tickets[idx] = ticket
                with open("tickets.json", "w", encoding="utf-8") as f:
                    json.dump(tickets, f, indent=4, ensure_ascii=False)
                st.success("Mensagem enviada com sucesso.")
                st.rerun()
            else:
                st.warning("Digite algo para enviar.")

        st.markdown("---")

        # Exibe as mensagens do chat em ordem invertida (mais recentes primeiro)
        if "mensagens" not in ticket:
            ticket["mensagens"] = []

        for m in reversed(ticket["mensagens"]):
            remetente = m["usuario"]
            hora = m["data"]
            texto = m["mensagem"]
            eh_usuario = remetente == st.session_state.get("username")

            col1, col2 = st.columns([6, 1]) if eh_usuario else st.columns([1, 6])

            with (col1 if eh_usuario else col2):
                st.markdown(
                    f"""
                    <div style='
                        background-color: {"#C6E8F8" if eh_usuario else "#F1F0F0"};
                        padding: 10px 15px;
                        border-radius: 10px;
                        margin-bottom: 5px;
                        max-width: 100%;
                        word-wrap: break-word;
                        box-shadow: 1px 1px 3px rgba(0,0,0,0.1);
                    '>
                        <strong>{remetente}</strong> <span style='font-size: 10px; color: #555;'>({hora})</span><br>
                        {texto}
                    </div>
                    """,
                    unsafe_allow_html=True
                )


    if st.button("🔙 Voltar"):
        st.session_state["pagina_atual"] = "principal"
        st.rerun()

def pagina_login():
    usuarios = carregar_usuarios()

    # Layout centralizado com colunas
    col1, col2, col3 = st.columns([1, 2, 1])  # coluna do meio é onde vai o formulário

    with col2:
        st.title("PORTAL DE TICKETS")
        st.markdown("### Login")

        email = st.text_input("E-mail", key="login_email").strip().lower()
        senha = st.text_input("Senha", type="password", key="login_senha")

        if st.button("Entrar"):
            if autenticar_usuario(email, senha, usuarios):
                st.session_state['logged_in'] = True
                st.session_state['username'] = usuarios[email]["nome"]
                st.session_state['email'] = email
                st.session_state['pagina_atual'] = "principal"  # Redireciona para a página principal
                st.rerun()
            else:
                st.error("E-mail ou senha incorretos.")

        st.info("Não possui uma conta? Solicite a criação de uma.")


if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'pagina_atual' not in st.session_state:
    st.session_state['pagina_atual'] = "login"

if st.session_state['logged_in']:
    if st.session_state["pagina_atual"] == "principal":
        pagina_principal()
    elif st.session_state["pagina_atual"] == "ticket_detalhe":
        pagina_ticket_detalhe()
else:
    pagina_login()

st.markdown(
f"""
    <style>
        :root {{
            --button-bg-light: #FFD700;
            --primary-color-light: #2e2e2e;
        }}
        .stButton > button {{
            background-color: {"var(--button-bg-light)"}; 
            color: {"var(--primary-color-light)"}; /* Cor do texto do botão */
            border: none;
            border-radius: 8px;
            padding: 10px 20px;
        }}
        .stButton > button:hover {{
            background-color: {'#FFCC00'};
            color: var(--primary-color-light);
        }}
    </style>
""",
    unsafe_allow_html=True
)

#Testar / Esconde menus do lit

#hide_streamlit_style = """
#    <style>
#    #MainMenu {visibility: hidden;}
#    footer {visibility: hidden;}
#    </style>
#"""
#st.markdown(hide_streamlit_style, unsafe_allow_html=True)
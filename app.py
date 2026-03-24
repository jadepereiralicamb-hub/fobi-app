import locale
from datetime import datetime

import streamlit as st
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# =========================
# CONFIG GERAL
# =========================
st.set_page_config(page_title="FOBI - Intervenção Ambiental", page_icon="📄")

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/documents",
]

TEMPLATE_ID = "1kwLTcVTem1clj_to_YjuQyBCYMenSrIBBJJBhSSnjMo"
PASTA_ID = "1ir6pbTBPGKwUJPyx2KmZO4bl3lnybPVT"


# =========================
# OAUTH
# =========================
def get_client_config():
    return {
        "web": {
            "client_id": st.secrets["google_oauth"]["client_id"],
            "client_secret": st.secrets["google_oauth"]["client_secret"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [st.secrets["google_oauth"]["redirect_uri"]],
        }
    }


def get_flow(state=None):
    flow = Flow.from_client_config(
        get_client_config(),
        scopes=SCOPES,
        state=state,
    )
    flow.redirect_uri = st.secrets["google_oauth"]["redirect_uri"]
    return flow


def start_google_login():
    flow = get_flow()

    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )

    st.session_state["oauth_state"] = state
    st.link_button("Entrar com Google", authorization_url)


def handle_oauth_callback():
    query_params = st.query_params

    if "code" not in query_params:
        return

    code = query_params.get("code")
    returned_state = query_params.get("state")
    saved_state = st.session_state.get("oauth_state")

    if saved_state and returned_state != saved_state:
        st.error("Falha na validação do login. Tente novamente.")
        st.stop()

    try:
        flow = get_flow(state=saved_state)
        flow.fetch_token(code=code)

        creds = flow.credentials

        st.session_state["google_token"] = {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": list(creds.scopes) if creds.scopes else SCOPES,
        }

        # limpa query params depois do login
        st.query_params.clear()
        st.session_state["oauth_state"] = None
        st.success("Login com Google realizado com sucesso.")
        st.rerun()

    except Exception as e:
        st.error(f"Erro ao concluir login com Google: {e}")
        st.stop()


def get_user_credentials():
    token_data = st.session_state.get("google_token")
    if not token_data:
        return None

    creds = Credentials(
        token=token_data["token"],
        refresh_token=token_data.get("refresh_token"),
        token_uri=token_data["token_uri"],
        client_id=token_data["client_id"],
        client_secret=token_data["client_secret"],
        scopes=token_data["scopes"],
    )

    # renova token se necessário
    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            st.session_state["google_token"] = {
                "token": creds.token,
                "refresh_token": creds.refresh_token,
                "token_uri": creds.token_uri,
                "client_id": creds.client_id,
                "client_secret": creds.client_secret,
                "scopes": list(creds.scopes) if creds.scopes else SCOPES,
            }
        except Exception:
            st.session_state.pop("google_token", None)
            return None

    return creds


def logout():
    st.session_state.pop("google_token", None)
    st.session_state.pop("oauth_state", None)
    st.query_params.clear()
    st.rerun()


def get_google_services():
    creds = get_user_credentials()
    if not creds:
        return None, None

    docs_service = build("docs", "v1", credentials=creds)
    drive_service = build("drive", "v3", credentials=creds)
    return docs_service, drive_service


# =========================
# AUXILIARES
# =========================
def data_ptbr():
    try:
        locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")
        return datetime.now().strftime("%d de %B de %Y")
    except locale.Error:
        meses = {
            1: "janeiro",
            2: "fevereiro",
            3: "março",
            4: "abril",
            5: "maio",
            6: "junho",
            7: "julho",
            8: "agosto",
            9: "setembro",
            10: "outubro",
            11: "novembro",
            12: "dezembro",
        }
        hoje = datetime.now()
        return f"{hoje.day} de {meses[hoje.month]} de {hoje.year}"


def montar_texto_exigencias(
    requerimento_incompleto,
    quantidade_arvores,
    supressao,
    possui_app,
    procurador,
    requerente_proprietario,
    compensacao,
):
    texto = []

    if requerimento_incompleto:
        texto.append(
            "Considerando que o requerimento apresenta informações incompletas, "
            "deverá apresentar versão retificada e assinada em todas as páginas.\n"
        )

    if quantidade_arvores:
        texto.append(
            "Item 5.1.4: Informar quantidade de árvores isoladas suprimidas.\n"
        )

    texto.append("Apresentar os documentos conforme item 12:\n")

    texto.append(
        "- Documento de identificação do requerente;\n"
        "- Documento do proprietário do imóvel;\n"
        "- Documento do imóvel;\n"
        "- Cadastro Ambiental Rural (CAR);\n"
        "- Roteiro de acesso com imagem de satélite;\n"
    )

    if supressao == "Sim":
        texto.append(
            "- Laudo técnico com ART sobre espécies ameaçadas conforme Decreto 47.749/2019;\n"
        )

    if possui_app == "Sim":
        texto.append(
            "- Delimitação de APP conforme Lei 20.922/2013;\n"
        )

    if procurador == "Sim":
        texto.append(
            "- Procuração com documentos do procurador;\n"
        )

    if requerente_proprietario == "Não":
        texto.append(
            "- Contrato e carta de anuência;\n"
        )

    texto.append(
        "- Levantamento planimétrico com ART e arquivo KML contendo:\n"
        "  * Área do lote\n"
        "  * APP (quando houver)\n"
        "  * Áreas de intervenção\n"
        "  * Árvores a suprimir\n"
    )

    if compensacao == "Mudas":
        texto.append(
            "- Atender Resolução Codema nº 04/2018 (doação de mudas);\n"
        )
    else:
        texto.append(
            "- Apresentar ofício solicitando compensação pecuniária;\n"
        )

    texto.append(
        "- Comprovante de pagamento das taxas municipais conforme Lei 6.584/2021.\n"
    )

    return "\n".join(texto)


def gerar_fobi(
    docs_service,
    drive_service,
    numero_processo,
    interessado,
    endereco,
    matricula,
    requerimento_incompleto,
    quantidade_arvores,
    supressao,
    possui_app,
    procurador,
    requerente_proprietario,
    compensacao,
):
    texto_final = montar_texto_exigencias(
        requerimento_incompleto,
        quantidade_arvores,
        supressao,
        possui_app,
        procurador,
        requerente_proprietario,
        compensacao,
    )

    # Lê o template como texto
    conteudo_template = drive_service.files().export_media(
        fileId=TEMPLATE_ID,
        mimeType="text/plain",
    ).execute().decode("utf-8")

    dados = {
        "{{numero_processo}}": numero_processo,
        "{{interessado}}": interessado,
        "{{endereco}}": endereco,
        "{{matricula}}": matricula,
        "{{data}}": data_ptbr(),
        "{{responsavel}}": "Poliana Carolina Maia",
        "{{texto_exigencias}}": texto_final,
    }

    for chave, valor in dados.items():
        conteudo_template = conteudo_template.replace(chave, valor or "")

    # Cria novo Google Doc
    novo_doc = docs_service.documents().create(
        body={"title": f"FOBI - {numero_processo}"}
    ).execute()

    doc_id = novo_doc["documentId"]

    # Insere o texto
    docs_service.documents().batchUpdate(
        documentId=doc_id,
        body={
            "requests": [
                {
                    "insertText": {
                        "location": {"index": 1},
                        "text": conteudo_template,
                    }
                }
            ]
        },
    ).execute()

    # Move para a pasta de destino
    arquivo_atual = drive_service.files().get(
        fileId=doc_id,
        fields="parents",
        supportsAllDrives=True,
    ).execute()

    parents_atuais = ",".join(arquivo_atual.get("parents", []))

    update_kwargs = {
        "fileId": doc_id,
        "addParents": PASTA_ID,
        "supportsAllDrives": True,
    }

    if parents_atuais:
        update_kwargs["removeParents"] = parents_atuais

    drive_service.files().update(**update_kwargs).execute()

    return doc_id


# =========================
# APP
# =========================
handle_oauth_callback()

st.title("FOBI - Intervenção Ambiental")

creds = get_user_credentials()

col1, col2 = st.columns([3, 1])
with col1:
    if creds:
        st.success("Google conectado.")
    else:
        st.info("Faça login com sua conta Google para gerar o documento no seu Drive.")
with col2:
    if creds:
        st.button("Sair", on_click=logout)

if not creds:
    start_google_login()
    st.stop()

docs_service, drive_service = get_google_services()

numero_processo = st.text_input("Número do processo")
interessado = st.text_input("Interessado")
endereco = st.text_input("Endereço")
matricula = st.text_input("Matrícula")

st.subheader("Pendências do requerimento")
requerimento_incompleto = st.checkbox("Requerimento incompleto?")
quantidade_arvores = st.checkbox("Não informou quantidade de árvores?")

st.subheader("Características")
supressao = st.radio("Haverá supressão?", ["Sim", "Não"])
possui_app = st.radio("Intervenção em APP?", ["Sim", "Não"])
procurador = st.radio("Possui procurador?", ["Sim", "Não"])
requerente_proprietario = st.radio("Requerente é proprietário?", ["Sim", "Não"])

st.subheader("Compensação ambiental")
compensacao = st.radio("Tipo", ["Mudas", "Pecuniária"])

if st.button("Gerar FOBI", type="primary"):
    if not numero_processo.strip():
        st.error("Informe o número do processo.")
        st.stop()

    try:
        doc_id = gerar_fobi(
            docs_service=docs_service,
            drive_service=drive_service,
            numero_processo=numero_processo.strip(),
            interessado=interessado.strip(),
            endereco=endereco.strip(),
            matricula=matricula.strip(),
            requerimento_incompleto=requerimento_incompleto,
            quantidade_arvores=quantidade_arvores,
            supressao=supressao,
            possui_app=possui_app,
            procurador=procurador,
            requerente_proprietario=requerente_proprietario,
            compensacao=compensacao,
        )

        st.success("FOBI gerado com sucesso.")
        st.link_button(
            "Abrir documento no Google Docs",
            f"https://docs.google.com/document/d/{doc_id}/edit",
        )

    except HttpError as e:
        st.error(f"Erro Google API: {e}")
    except Exception as e:
        st.error(f"Erro inesperado: {e}")

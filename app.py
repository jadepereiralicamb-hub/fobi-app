import locale
from datetime import datetime

import streamlit as st
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

st.set_page_config(page_title="FOBI - Intervenção Ambiental", page_icon="📄")

TEMPLATE_ID = "1kwLTcVTem1clj_to_YjuQyBCYMenSrIBBJJBhSSnjMo"
PASTA_ID = "1ir6pbTBPGKwUJPyx2KmZO4bl3lnybPVT"


def get_google_services():
    tokens = getattr(st.user, "tokens", None)
    if not tokens:
        st.error("Tokens não disponíveis. Verifique a configuração de autenticação.")
        st.stop()

    access_token = tokens.get("access")
    if not access_token:
        st.error("Access token não disponível.")
        st.stop()

    creds = Credentials(token=access_token)
    docs_service = build("docs", "v1", credentials=creds)
    drive_service = build("drive", "v3", credentials=creds)
    return docs_service, drive_service


def data_ptbr():
    try:
        locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")
        return datetime.now().strftime("%d de %B de %Y")
    except locale.Error:
        meses = {
            1: "janeiro", 2: "fevereiro", 3: "março", 4: "abril",
            5: "maio", 6: "junho", 7: "julho", 8: "agosto",
            9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro"
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
        texto.append("Item 5.1.4: Informar quantidade de árvores isoladas suprimidas.\n")

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
        texto.append("- Delimitação de APP conforme Lei 20.922/2013;\n")

    if procurador == "Sim":
        texto.append("- Procuração com documentos do procurador;\n")

    if requerente_proprietario == "Não":
        texto.append("- Contrato e carta de anuência;\n")

    texto.append(
        "- Levantamento planimétrico com ART e arquivo KML contendo:\n"
        "  * Área do lote\n"
        "  * APP (quando houver)\n"
        "  * Áreas de intervenção\n"
        "  * Árvores a suprimir\n"
    )

    if compensacao == "Mudas":
        texto.append("- Atender Resolução Codema nº 04/2018 (doação de mudas);\n")
    else:
        texto.append("- Apresentar ofício solicitando compensação pecuniária;\n")

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

    novo_doc = docs_service.documents().create(
        body={"title": f"FOBI - {numero_processo}"}
    ).execute()

    doc_id = novo_doc["documentId"]

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


def is_logged_in():
    return getattr(st.user, "is_logged_in", False)


st.title("FOBI - Intervenção Ambiental")

col1, col2 = st.columns([3, 1])

with col1:
    if is_logged_in():
        nome = getattr(st.user, "name", None) or getattr(st.user, "email", "Usuário")
        st.success(f"Google conectado: {nome}")
    else:
        st.info("Faça login com sua conta Google para gerar o documento no seu Drive.")

with col2:
    if is_logged_in():
        st.button("Sair", on_click=st.logout)

if not is_logged_in():
    st.button("Entrar com Google", on_click=st.login, type="primary")
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

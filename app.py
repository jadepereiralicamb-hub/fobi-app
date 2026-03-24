import streamlit as st
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from datetime import datetime

# =========================
# CONFIG GOOGLE
# =========================
SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive'
]

creds = Credentials.from_service_account_info(
    st.secrets["gcp"], scopes=SCOPES)

docs_service = build('docs', 'v1', credentials=creds)
drive_service = build('drive', 'v3', credentials=creds)

TEMPLATE_ID = "1kwLTcVTem1clj_to_YjuQyBCYMenSrIBBJJBhSSnjMo"
PASTA_ID = "1ir6pbTBPGKwUJPyx2KmZO4bl3lnybPVT"

# =========================
# INTERFACE
# =========================
st.title("FOBI - Intervenção Ambiental")

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

# =========================
# GERAR FOBI
# =========================
if st.button("Gerar FOBI"):

    texto = []

    # Pendências
    if requerimento_incompleto:
        texto.append(
            "Considerando que o requerimento apresenta informações incompletas, deverá apresentar versão retificada e assinada em todas as páginas.\n"
        )

    if quantidade_arvores:
        texto.append(
            "Item 5.1.4: Informar quantidade de árvores isoladas suprimidas.\n"
        )

    texto.append("Apresentar os documentos conforme item 12:\n")

    # Documentos base
    texto.append(
        "- Documento de identificação do requerente;\n"
        "- Documento do proprietário do imóvel;\n"
        "- Documento do imóvel;\n"
        "- Cadastro Ambiental Rural (CAR);\n"
        "- Roteiro de acesso com imagem de satélite;\n"
    )

    # Supressão
    if supressao == "Sim":
        texto.append(
            "- Laudo técnico com ART sobre espécies ameaçadas conforme Decreto 47.749/2019;\n"
        )

    # APP
    if possui_app == "Sim":
        texto.append(
            "- Delimitação de APP conforme Lei 20.922/2013;\n"
        )

    # Procurador
    if procurador == "Sim":
        texto.append(
            "- Procuração com documentos do procurador;\n"
        )

    # Não proprietário
    if requerente_proprietario == "Não":
        texto.append(
            "- Contrato e carta de anuência;\n"
        )

    # Georreferenciamento
    texto.append(
        "- Levantamento planimétrico com ART e arquivo KML contendo:\n"
        "  * Área do lote\n"
        "  * APP (quando houver)\n"
        "  * Áreas de intervenção\n"
        "  * Árvores a suprimir\n"
    )

    # Compensação
    if compensacao == "Mudas":
        texto.append(
            "- Atender Resolução Codema nº 04/2018 (doação de mudas);\n"
        )
    else:
        texto.append(
            "- Apresentar ofício solicitando compensação pecuniária;\n"
        )

    # Taxas
    texto.append(
        "- Comprovante de pagamento das taxas municipais conforme Lei 6.584/2021.\n"
    )

    texto_final = "\n".join(texto)

    # =========================
    # LER TEMPLATE COMO TEXTO
    # =========================
    conteudo_template = drive_service.files().export_media(
        fileId=TEMPLATE_ID,
        mimeType="text/plain"
    ).execute().decode("utf-8")

    # =========================
    # SUBSTITUIR VARIÁVEIS
    # =========================
    dados = {
        "{{numero_processo}}": numero_processo,
        "{{interessado}}": interessado,
        "{{endereco}}": endereco,
        "{{matricula}}": matricula,
        "{{data}}": datetime.now().strftime("%d de %B de %Y"),
        "{{responsavel}}": "Poliana Carolina Maia",
        "{{texto_exigencias}}": texto_final
    }

    for chave, valor in dados.items():
        conteudo_template = conteudo_template.replace(chave, valor)

    # =========================
    # CRIAR NOVO DOC
    # =========================
    novo_doc = docs_service.documents().create(
        body={"title": f"FOBI - {numero_processo}"}
    ).execute()

    doc_id = novo_doc["documentId"]

    # =========================
    # INSERIR TEXTO
    # =========================
    docs_service.documents().batchUpdate(
        documentId=doc_id,
        body={
            "requests": [
                {
                    "insertText": {
                        "location": {"index": 1},
                        "text": conteudo_template
                    }
                }
            ]
        }
    ).execute()

    # =========================
    # MOVER PARA PASTA
    # =========================
    drive_service.files().update(
        fileId=doc_id,
        addParents=PASTA_ID,
        removeParents="root"
    ).execute()

    st.success("FOBI gerado com sucesso!")
    st.write(f"https://docs.google.com/document/d/{doc_id}")

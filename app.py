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
PASTA_ID = "1qZL1hwnug71MlVz565gw43jm_8ldHLI-"

# =========================
# FORMULÁRIO
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
# GERAR TEXTO
# =========================
if st.button("Gerar FOBI"):

    texto = []

    # Pendência
    if requerimento_incompleto:
        texto.append("""
Considerando que o requerimento apresenta informações incompletas, deverá apresentar versão retificada e assinada em todas as páginas.
""")

    if quantidade_arvores:
        texto.append("""
Item 5.1.4: Informar quantidade de árvores isoladas suprimidas.
""")

    texto.append("Apresentar os documentos conforme item 12:\n")

    # Documentos base
    texto.append("""
- Documento de identificação do requerente;
- Documento do proprietário do imóvel;
- Documento do imóvel;
- Cadastro Ambiental Rural (CAR);
- Roteiro de acesso com imagem de satélite;
""")

    # Supressão
    if supressao == "Sim":
        texto.append("""
- Laudo técnico com ART sobre espécies ameaçadas conforme Decreto 47.749/2019;
""")

    # APP
    if possui_app == "Sim":
        texto.append("""
- Delimitação de APP conforme Lei 20.922/2013;
""")

    # Procurador
    if procurador == "Sim":
        texto.append("""
- Procuração com documentos do procurador;
""")

    # Não proprietário
    if requerente_proprietario == "Não":
        texto.append("""
- Contrato e carta de anuência;
""")

    # Georreferenciamento
    texto.append("""
- Levantamento planimétrico com ART e arquivo KML contendo:
  * Área do lote
  * APP (quando houver)
  * Áreas de intervenção
  * Árvores a suprimir
""")

    # Compensação
    if compensacao == "Mudas":
        texto.append("""
- Atender Resolução Codema nº 04/2018 (doação de mudas);
""")
    else:
        texto.append("""
- Apresentar ofício solicitando compensação pecuniária;
""")

    # Taxas
    texto.append("""
- Comprovante de pagamento das taxas municipais conforme Lei 6.584/2021.
""")

    texto_final = "\n".join(texto)

    # ==========================
    # GERAR DOCS
    # =========================
    copia = drive_service.files().copy(
        fileId=TEMPLATE_ID,
        body={"name": f"FOBI - {numero_processo}",
              "parents": [PASTA_ID]}
    ).execute()

    doc_id = copia['id']

    dados = {
        "{{numero_processo}}": numero_processo,
        "{{interessado}}": interessado,
        "{{endereco}}": endereco,
        "{{matricula}}": matricula,
        "{{data}}": datetime.now().strftime("%d de %B de %Y"),
        "{{responsavel}}": "Poliana Carolina Maia",
        "{{texto_exigencias}}": texto_final
    }

    requests = []
    for k, v in dados.items():
        requests.append({
            'replaceAllText': {
                'containsText': {'text': k, 'matchCase': True},
                'replaceText': v
            }
        })

    docs_service.documents().batchUpdate(
        documentId=doc_id,
        body={'requests': requests}
    ).execute()

    st.success("FOBI gerado com sucesso!")
    st.write(f"https://docs.google.com/document/d/{doc_id}")

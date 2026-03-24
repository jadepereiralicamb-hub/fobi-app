import streamlit as st

st.title("Gerador de FOBI - Intervenção Ambiental")

# =========================
# DADOS BÁSICOS
# =========================
numero_processo = st.text_input("Número do Processo")
interessado = st.text_input("Interessado")
endereco = st.text_input("Endereço")
matricula = st.text_input("Matrícula")

st.divider()

# =========================
# PERGUNTAS CONDICIONAIS
# =========================
supressao = st.radio("Haverá supressão de vegetação?", ["Sim", "Não"])
possui_app = st.radio("Há intervenção em APP?", ["Sim", "Não"])
procurador = st.radio("Possui procurador?", ["Sim", "Não"])

tipo_compensacao = st.selectbox(
    "Tipo de compensação ambiental",
    ["Doação de mudas", "Pecuniária"]
)

st.divider()

# =========================
# BLOCOS PADRÃO
# =========================
TEXTO_BASE = """
Após análise do Requerimento para Autorização de Intervenção Ambiental, o Departamento de Licenciamento Ambiental – DLA, vem por meio deste solicitar apresentação de informações complementares abaixo indicadas, no prazo de 60 (sessenta dias).
"""

BLOCO_SUPRESSAO = """
- Laudo Técnico, assinado por profissional habilitado, quanto à existência de espécies ameaçadas, conforme Decreto 47.749/2019;
"""

BLOCO_APP = """
- Apresentar delimitação de Área de Preservação Permanente (APP), conforme Lei Estadual 20.922/2013;
"""

BLOCO_PROCURACAO = """
- Procuração acompanhada de documentos pessoais do procurador;
"""

BLOCO_MUDAS = """
- Apresentar documentação para compensação ambiental via doação de mudas (Resolução Codema nº 04/2018);
"""

BLOCO_PECUNIARIO = """
- Apresentar ofício solicitando compensação ambiental via recolhimento pecuniário;
"""

BLOCO_FIXOS = """
- Documento de identificação do requerente;
- Documento do imóvel;
- Cadastro Ambiental Rural (CAR);
- Comprovante de pagamento das taxas municipais;
"""

# =========================
# GERAÇÃO DO FOBI
# =========================
if st.button("Gerar FOBI"):

    texto = [TEXTO_BASE, BLOCO_FIXOS]

    if supressao == "Sim":
        texto.append(BLOCO_SUPRESSAO)

    if possui_app == "Sim":
        texto.append(BLOCO_APP)

    if procurador == "Sim":
        texto.append(BLOCO_PROCURACAO)

    if tipo_compensacao == "Doação de mudas":
        texto.append(BLOCO_MUDAS)
    else:
        texto.append(BLOCO_PECUNIARIO)

    fobi = f"""
FORMULÁRIO DE ORIENTAÇÃO BÁSICO INTEGRADO – FOBI

PRO {numero_processo}

INTERESSADO:
{interessado}

TIPO DE PROCESSO:
INTERVENÇÃO AMBIENTAL

ENDEREÇO:
{endereco}

MATRÍCULA:
{matricula}

{''.join(texto)}

Pará de Minas, ____ de __________ de 2026.

____________________________________________
Departamento de Licenciamento Ambiental
"""

    st.text_area("FOBI Gerado", fobi, height=500)

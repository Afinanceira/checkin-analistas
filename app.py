from datetime import date
from io import BytesIO
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
import requests
import streamlit as st

# ==========================================
# CONFIGURAÇÃO DO FIREBASE REALTIME DATABASE
# ==========================================
FIREBASE_URL = "https://escala-nova-d596e-default-rtdb.firebaseio.com/checkins.json"


def salvar_checkin_firebase(dados):
  try:
    response = requests.post(FIREBASE_URL, json=dados)
    return response.status_code == 200
  except Exception as e:
    st.error(f"Erro ao conectar com Firebase: {e}")
    return False


def buscar_checkins_firebase():
  try:
    response = requests.get(FIREBASE_URL)
    if response.status_code == 200 and response.json():
      dados_dict = response.json()
      # Converte o dicionário retornado pelo Firebase em uma lista
      lista_dados = []
      for key, val in dados_dict.items():
        val["id"] = key
        lista_dados.append(val)
      return pd.DataFrame(lista_dados)
    return pd.DataFrame()
  except Exception as e:
    st.error(f"Erro ao buscar dados do Firebase: {e}")
    return pd.DataFrame()


# Lista de Demandas/Checklist Diário
TAREFAS = [
    "1. Verificação de Pendências e Filas",
    "2. Acompanhamento dos Avisos e Canais",
    "3. Leitura e Checagem do Flash",
    "4. Monitoramento e Identificação de Instabilidades",
    "5. Criação e Atualização de Atalhos",
    "6. Passagem de Bastão e Registros do Turno",
]

ANALISTAS = ["Leandro", "Tarcyla", "Ivah"]

st.set_page_config(
    page_title="Check-in Diário da Equipe", page_icon="🔥", layout="wide"
)

# ==========================================
# GERADOR DE PDF COM REPORTLAB
# ==========================================


def gerar_pdf_relatorio(df_analista, nome_analista):
  buffer = BytesIO()
  doc = SimpleDocTemplate(
      buffer,
      pagesize=letter,
      rightMargin=30,
      leftMargin=30,
      topMargin=30,
      bottomMargin=30,
  )
  elements = []
  styles = getSampleStyleSheet()

  title_style = ParagraphStyle(
      "TitleStyle",
      parent=styles["Heading1"],
      fontSize=18,
      textColor=colors.HexColor("#1E3A8A"),
      spaceAfter=12,
  )

  elements.append(
      Paragraph(
          f"<b>Relatório de Desempenho (30 Dias) - {nome_analista}</b>",
          title_style,
      )
  )
  elements.append(Spacer(1, 10))

  total_registros = len(df_analista)
  total_possivel = total_registros * 6
  total_concluido = (
      df_analista[["p1", "p2", "p3", "p4", "p5", "p6"]].sum().sum()
      if total_registros > 0
      else 0
  )

  taxa_eficiencia = (
      (total_concluido / total_possivel * 100) if total_possivel > 0 else 0
  )

  resumo_text = f"""
    <b>Período Avaliado:</b> {total_registros} / 30 Dias Registrados<br/>
    <b>Tarefas Concluídas:</b> {total_concluido} de {total_possivel} itens esperados<br/>
    <b>Taxa Geral de Eficiência:</b> {taxa_eficiencia:.1f}%
    """
  elements.append(Paragraph(resumo_text, styles["Normal"]))
  elements.append(Spacer(1, 15))

  dados_tabela = [
      ["Dia", "Data", "P1", "P2", "P3", "P4", "P5", "P6", "Observações"]
  ]

  for _, row in df_analista.iterrows():
    obs = row["observacoes"] if row["observacoes"] else "-"
    dados_tabela.append([
        f"Dia {row['dia_trabalho']}",
        row["data"],
        "✅" if row["p1"] else "❌",
        "✅" if row["p2"] else "❌",
        "✅" if row["p3"] else "❌",
        "✅" if row["p4"] else "❌",
        "✅" if row["p5"] else "❌",
        "✅" if row["p6"] else "❌",
        Paragraph(obs, styles["BodyText"]),
    ])

  tabela = Table(
      dados_tabela, colWidths=[40, 65, 25, 25, 25, 25, 25, 25, 250]
  )
  tabela.setStyle(
      TableStyle([
          ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
          ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
          ("ALIGN", (0, 0), (-1, -1), "CENTER"),
          ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
          ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
          ("FONTSIZE", (0, 0), (-1, -1), 8),
          ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
          ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F3F4F6")),
          ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
      ])
  )
  elements.append(tabela)
  elements.append(Spacer(1, 20))

  if taxa_eficiencia >= 85:
    conclusao_txt = f"<b>Conclusão de Eficiência:</b> O(a) analista {nome_analista} obteve um desempenho <b>EXCELENTE</b> ({taxa_eficiencia:.1f}%), demonstrando altíssimo engajamento no cumprimento diário de processos e rotinas operacionais."
  elif taxa_eficiencia >= 70:
    conclusao_txt = f"<b>Conclusão de Eficiência:</b> O(a) analista {nome_analista} apresentou um desempenho <b>BOM</b> ({taxa_eficiencia:.1f}%), mantendo boa regularidade, com oportunidades pontuais de melhoria na consistência diária."
  else:
    conclusao_txt = f"<b>Conclusão de Eficiência:</b> O(a) analista {nome_analista} registrou uma taxa de <b>ATENÇÃO</b> ({taxa_eficiencia:.1f}%). Recomenda-se alinhar em feedback os pontos de travamento ou esquecimento das rotinas marcadas com ❌."

  elements.append(
      Paragraph(
          conclusao_txt,
          ParagraphStyle(
              "ConcStyle",
              parent=styles["Normal"],
              borderColor=colors.HexColor("#1E3A8A"),
              borderWidth=1,
              borderPadding=8,
              backColor=colors.HexColor("#EFF6FF"),
          ),
      )
  )

  doc.build(elements)
  buffer.seek(0)
  return buffer


# ==========================================
# INTERFACE DO USUÁRIO (STREAMLIT)
# ==========================================
st.title("🔥 Sistema de Check-in Diário (Firebase)")

aba1, aba2 = st.tabs([
    "📝 Realizar Check-in Diário",
    "📊 Relatórios & PDFs (Supervisão)",
])

# ----- ABA 1: FORMULÁRIO DE CHECK-IN -----
with aba1:
  st.subheader("Registrar Rotina Operacional")

  col_a, col_b, col_c = st.columns(3)
  with col_a:
    analista = st.selectbox("Selecione o Analista:", ANALISTAS)
  with col_b:
    dia_trabalho = st.number_input(
        "Dia de Trabalho (1 a 30):", min_value=1, max_value=30, value=1
    )
  with col_c:
    data_hoje = st.date_input("Data:", date.today())

  st.write("---")
  st.markdown("### 📋 Marque as demandas concluídas no dia:")

  p1 = st.checkbox(TAREFAS[0])
  p2 = st.checkbox(TAREFAS[1])
  p3 = st.checkbox(TAREFAS[2])
  p4 = st.checkbox(TAREFAS[3])
  p5 = st.checkbox(TAREFAS[4])
  p6 = st.checkbox(TAREFAS[5])

  obs = st.text_area(
      "Observações/Justificativas do dia (opcional):",
      placeholder="Ex: Instabilidade no sistema entre 14h e 15h.",
  )

  if st.button("💾 Salvar Check-in no Firebase", type="primary"):
    payload = {
        "data": str(data_hoje),
        "dia_trabalho": int(dia_trabalho),
        "analista": analista,
        "p1": int(p1),
        "p2": int(p2),
        "p3": int(p3),
        "p4": int(p4),
        "p5": int(p5),
        "p6": int(p6),
        "observacoes": obs,
    }

    if salvar_checkin_firebase(payload):
      st.success(
          f"Check-in do Dia {dia_trabalho} para {analista} salvo com sucesso na"
          " nuvem!"
      )
    else:
      st.error("Não foi possível salvar os dados. Verifique a conexão.")

# ----- ABA 2: RELATÓRIOS E GERADOR DE PDF -----
with aba2:
  st.subheader("Painel de Acompanhamento (Em Tempo Real)")

  df = buscar_checkins_firebase()

  if not df.empty:
    analista_sel = st.selectbox(
        "Filtrar por Analista para Relatório:", ANALISTAS
    )
    df_filtrado = (
        df[df["analista"] == analista_sel]
        .sort_values(by="dia_trabalho")
        .reset_index(drop=True)
    )

    if not df_filtrado.empty:
      st.write(
          f"### Histórico de Registros - {analista_sel} ({len(df_filtrado)}/30"
          " dias)"
      )
      st.dataframe(
          df_filtrado[
              [
                  "dia_trabalho",
                  "data",
                  "p1",
                  "p2",
                  "p3",
                  "p4",
                  "p5",
                  "p6",
                  "observacoes",
              ]
          ],
          use_container_width=True,
      )

      pdf_bytes = gerar_pdf_relatorio(df_filtrado, analista_sel)

      st.download_button(
          label=f"📄 Baixar Relatório PDF de {analista_sel}",
          data=pdf_bytes,
          file_name=f"Relatorio_30Dias_{analista_sel}.pdf",
          mime="application/pdf",
          type="primary",
      )
    else:
      st.info(f"Nenhum registro encontrado no Firebase para {analista_sel}.")
  else:
    st.info("Nenhum check-in registrado no banco de dados até o momento.")

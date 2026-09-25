from datetime import date
from io import BytesIO
import pandas as pd
import plotly.express as px
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
import requests
import streamlit as st

# ==========================================
# CONFIGURAÇÃO DE DESIGN & STREAMLIT
# ==========================================
st.set_page_config(
    page_title="Gestão de Desempenho | Operações",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

FIREBASE_URL = "https://escala-nova-d596e-default-rtdb.firebaseio.com/checkins.json"
ANALISTAS = ["Leandro", "Tarcyla", "Ivah"]

TAREFAS = [
    "1. Varredura de Pendências & Filas de Atendimento",
    "2. Leitura & Checagem das Regras no Flash",
    "3. Confirmação de Leitura nos Canais de Avisos",
    "4. Monitoramento de Instabilidades & Provedores",
    "5. Criação/Atualização de Atalhos & Macros",
    "6. Passagem de Bastão & Log de Ocorrências",
]


# ==========================================
# FUNÇÕES DE INTEGRAÇÃO FIREBASE
# ==========================================
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
      lista_dados = []
      for key, val in dados_dict.items():
        val["id"] = key
        lista_dados.append(val)
      return pd.DataFrame(lista_dados)
    return pd.DataFrame()
  except Exception as e:
    st.error(f"Erro ao buscar dados do Firebase: {e}")
    return pd.DataFrame()


# ==========================================
# GERADOR DE PDF PROFISSIONAL & EXECUTIVO
# ==========================================
def gerar_pdf_executivo(
    df_analista, nome_analista, nota_supervisao, parecer_supervisao
):
  buffer = BytesIO()
  doc = SimpleDocTemplate(
      buffer,
      pagesize=letter,
      rightMargin=36,
      leftMargin=36,
      topMargin=36,
      bottomMargin=36,
  )
  elements = []
  styles = getSampleStyleSheet()

  # Estilos
  title_style = ParagraphStyle(
      "DocTitle",
      parent=styles["Heading1"],
      fontSize=20,
      leading=24,
      textColor=colors.HexColor("#0F172A"),
      fontName="Helvetica-Bold",
  )

  sub_style = ParagraphStyle(
      "SubTitle",
      parent=styles["Normal"],
      fontSize=10,
      textColor=colors.HexColor("#475569"),
      spaceAfter=15,
  )

  sec_title = ParagraphStyle(
      "SecTitle",
      parent=styles["Heading2"],
      fontSize=12,
      textColor=colors.HexColor("#1E3A8A"),
      spaceBefore=10,
      spaceAfter=6,
      fontName="Helvetica-Bold",
  )

  # Cabeçalho Executivo
  elements.append(
      Paragraph("RELATÓRIO EXECUTIVO DE DESEMPENHO", title_style)
  )
  elements.append(
      Paragraph(
          f"<b>Analista Avaliado:</b> {nome_analista} | <b>Emissão:</b>"
          f" {date.today().strftime('%d/%m/%Y')} | <b>Status:</b> Finalizado",
          sub_style,
      )
  )
  elements.append(Spacer(1, 5))

  # Métricas Consolidadas
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
  total_atalhos = (
      df_analista["qtd_atalhos"].sum() if "qtd_atalhos" in df_analista else 0
  )

  m_data = [[
      Paragraph(
          f"<b>Dias Registrados</b><br/><font size=14>{total_registros}/30</font>",
          styles["Normal"],
      ),
      Paragraph(
          f"<b>Taxa de Cumprimento</b><br/><font"
          f" size=14>{taxa_eficiencia:.1f}%</font>",
          styles["Normal"],
      ),
      Paragraph(
          f"<b>Atalhos Gerados</b><br/><font size=14>{total_atalhos}</font>",
          styles["Normal"],
      ),
      Paragraph(
          f"<b>Nota da Supervisão</b><br/><font"
          f" size=14>{nota_supervisao}/10</font>",
          styles["Normal"],
      ),
  ]]
  m_table = Table(m_data, colWidths=[130, 130, 130, 130])
  m_table.setStyle(
      TableStyle([
          ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
          ("ALIGN", (0, 0), (-1, -1), "CENTER"),
          ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
          ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
          ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
          ("TOPPADDING", (0, 0), (-1, -1), 8),
          ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
      ])
  )
  elements.append(m_table)
  elements.append(Spacer(1, 15))

  # Tabela Detalhada das Rotinas
  elements.append(Paragraph("Acompanhamento das Rotinas Diárias", sec_title))
  dados_tabela = [
      ["Dia", "Data", "Filas", "Flash", "Avisos", "Bugs", "Atalhos", "Handover"]
  ]

  for _, row in df_analista.iterrows():
    dados_tabela.append([
        f"Dia {row['dia_trabalho']}",
        row["data"],
        "✅" if row["p1"] else "❌",
        "✅" if row["p2"] else "❌",
        "✅" if row["p3"] else "❌",
        "✅" if row["p4"] else "❌",
        "✅" if row["p5"] else "❌",
        "✅" if row["p6"] else "❌",
    ])

  t_detalhe = Table(dados_tabela, colWidths=[55, 75, 65, 65, 65, 65, 65, 65])
  t_detalhe.setStyle(
      TableStyle([
          ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
          ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
          ("ALIGN", (0, 0), (-1, -1), "CENTER"),
          ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
          ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
          ("FONTSIZE", (0, 0), (-1, -1), 8),
          ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
          ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
      ])
  )
  elements.append(t_detalhe)
  elements.append(Spacer(1, 15))

  # Parecer Final da Supervisão
  elements.append(
      Paragraph("Parecer Técnico & Feedback da Supervisão", sec_title)
  )
  parecer_box = Paragraph(
      f"<b>Avaliação Oficial:</b> {parecer_supervisao}", styles["Normal"]
  )
  t_parecer = Table([[parecer_box]], colWidths=[520])
  t_parecer.setStyle(
      TableStyle([
          ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EFF6FF")),
          ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#3B82F6")),
          ("TOPPADDING", (0, 0), (-1, -1), 10),
          ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
          ("LEFTPADDING", (0, 0), (-1, -1), 10),
          ("RIGHTPADDING", (0, 0), (-1, -1), 10),
      ])
  )
  elements.append(t_parecer)

  doc.build(elements)
  buffer.seek(0)
  return buffer


# ==========================================
# INTERFACE PRINCIPAL DO STREAMLIT
# ==========================================
st.sidebar.title("⚙️ Operações & Supervisão")
st.sidebar.markdown(
    "Acompanhamento em tempo real da equipe de suporte e análise."
)

menu = st.sidebar.radio(
    "Navegação:",
    [
        "📝 Check-in Diário (Analista)",
        "📊 Dashboard & Métricas (Supervisão)",
        "🎯 Parecer & Emissão de PDF",
    ],
)

df_base = buscar_checkins_firebase()

# ------------------------------------------
# MENU 1: CHECK-IN DIÁRIO (ANALISTA)
# ------------------------------------------
if menu == "📝 Check-in Diário (Analista)":
  st.title("📝 Check-in Operacional Diário")
  st.caption(
      "Preencha o formulário ao final do turno para alimentar seu relatório"
      " individual de desempenho."
  )

  with st.container():
    c1, c2, c3 = st.columns(3)
    with c1:
      analista = st.selectbox("Analista Responsável:", ANALISTAS)
    with c2:
      dia_trabalho = st.number_input(
          "Dia de Trabalho (1 a 30):", min_value=1, max_value=30, value=1
      )
    with c3:
      data_hoje = st.date_input("Data de Registro:", date.today())

  st.write("---")
  st.subheader("📋 Validação de Processos Obrigatorios")

  col_t1, col_t2 = st.columns(2)
  with col_t1:
    p1 = st.checkbox(TAREFAS[0])
    p2 = st.checkbox(TAREFAS[1])
    p3 = st.checkbox(TAREFAS[2])
  with col_t2:
    p4 = st.checkbox(TAREFAS[3])
    p5 = st.checkbox(TAREFAS[4])
    p6 = st.checkbox(TAREFAS[5])

  st.write("---")
  st.subheader("💡 Entregas & Ocorrências Especiais")

  ca1, ca2 = st.columns(2)
  with ca1:
    qtd_atalhos = st.number_input(
        "Quantidade de Atalhos/Macros criados/atualizados hoje:",
        min_value=0,
        value=0,
    )
  with ca2:
    obs = st.text_area(
        "Observações / Registro de Instabilidades no Turno:",
        placeholder=(
            "Informe aqui qualquer travamento, problema com provedor ou"
            " ocorrência relevante."
        ),
    )

  if st.button("🚀 Enviar Check-in Diário", type="primary", use_container_width=True):
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
        "qtd_atalhos": int(qtd_atalhos),
        "observacoes": obs,
    }

    if salvar_checkin_firebase(payload):
      st.balloons()
      st.success(
          f"Check-in do Dia {dia_trabalho} enviado com sucesso para a base da"
          " supervisão!"
      )
    else:
      st.error("Falha ao salvar dados no banco de dados. Tente novamente.")

# ------------------------------------------
# MENU 2: DASHBOARD INTERATIVO
# ------------------------------------------
elif menu == "📊 Dashboard & Métricas (Supervisão)":
  st.title("📊 Painel de Controle e Métricas de Desempenho")

  if not df_base.empty:
    analista_sel = st.selectbox("Filtrar Visão Por Analista:", ANALISTAS)
    df_f = (
        df_base[df_base["analista"] == analista_sel]
        .sort_values(by="dia_trabalho")
        .reset_index(drop=True)
    )

    if not df_f.empty:
      # KPIs Superiores
      total_dias = len(df_f)
      total_possivel = total_dias * 6
      total_concluido = df_f[["p1", "p2", "p3", "p4", "p5", "p6"]].sum().sum()
      taxa_eficiencia = (
          (total_concluido / total_possivel * 100) if total_possivel > 0 else 0
      )
      total_atalhos = (
          df_f["qtd_atalhos"].sum() if "qtd_atalhos" in df_f else 0
      )

      k1, k2, k3, k4 = st.columns(4)
      k1.metric("Dias Registrados", f"{total_dias} / 30")
      k2.metric("Aproveitamento Geral", f"{taxa_eficiencia:.1f}%")
      k3.metric("Atalhos Criados", f"{total_atalhos}")
      k4.metric(
          "Status da Meta",
          "Excelente"
          if taxa_eficiencia >= 85
          else ("Regular" if taxa_eficiencia >= 70 else "Atenção"),
      )

      st.write("---")

      # Gráficos Interativos (Plotly)
      g1, g2 = st.columns(2)

      with g1:
        st.subheader("📈 Evolução da Eficiência por Dia")
        df_f["tarefas_dia"] = (
            df_f[["p1", "p2", "p3", "p4", "p5", "p6"]].sum(axis=1) / 6 * 100
        )
        fig_linha = px.line(
            df_f,
            x="dia_trabalho",
            y="tarefas_dia",
            markers=True,
            labels={"dia_trabalho": "Dia de Trabalho", "tarefas_dia": "Cumprimento (%)"},
            title=f"Consistência Diária - {analista_sel}",
        )
        fig_linha.update_yaxes(range=[0, 105])
        st.plotly_chart(fig_linha, use_container_width=True)

      with g2:
        st.subheader("🎯 Cumprimento por Categoria de Tarefa")
        totais_tarefas = [
            df_f["p1"].sum(),
            df_f["p2"].sum(),
            df_f["p3"].sum(),
            df_f["p4"].sum(),
            df_f["p5"].sum(),
            df_f["p6"].sum(),
        ]
        nomes_curtos = ["Filas", "Flash", "Avisos", "Bugs", "Atalhos", "Handover"]
        df_pizza = pd.DataFrame(
            {"Processo": nomes_curtos, "Concluídos": totais_tarefas}
        )
        fig_barras = px.bar(
            df_pizza,
            x="Processo",
            y="Concluídos",
            color="Processo",
            title="Distribuição de Tarefas Cumpridas",
        )
        st.plotly_chart(fig_barras, use_container_width=True)

      st.subheader("📋 Tabela Detalhada de Lançamentos")
      st.dataframe(df_f, use_container_width=True)

    else:
      st.info(f"Nenhum registro encontrado para {analista_sel}.")
  else:
    st.info("Nenhum dado cadastrado no sistema até o momento.")

# ------------------------------------------
# MENU 3: RELATÓRIO EXECUTIVO & PDF
# ------------------------------------------
elif menu == "🎯 Parecer & Emissão de PDF":
  st.title("🎯 Fechamento de Ciclo & Emissão de Relatório")

  if not df_base.empty:
    analista_sel = st.selectbox("Selecione o Analista para Fechamento:", ANALISTAS)
    df_f = (
        df_base[df_base["analista"] == analista_sel]
        .sort_values(by="dia_trabalho")
        .reset_index(drop=True)
    )

    if not df_f.empty:
      st.write("---")
      st.subheader(f"📝 Avaliação do Supervisor para {analista_sel}")

      nota = st.slider("Nota de Desempenho Geral (0 a 10):", 0.0, 10.0, 8.5, 0.5)
      parecer = st.text_area(
          "Parecer Técnico e Feedback da Supervisão:",
          value=(
              f"O(A) analista {analista_sel} demonstrou excelente"
              " compromisso com a rotina operacional ao longo do período,"
              " mantendo boa consistência na verificação do Flash e controle de"
              " pendências."
          ),
      )

      st.write("---")

      pdf_bytes = gerar_pdf_executivo(df_f, analista_sel, nota, parecer)

      st.download_button(
          label=f"📄 Gerar & Baixar Relatório Executivo em PDF ({analista_sel})",
          data=pdf_bytes,
          file_name=f"Relatorio_Executivo_{analista_sel}.pdf",
          mime="application/pdf",
          type="primary",
          use_container_width=True,
      )
    else:
      st.info(f"Sem dados suficientes para gerar relatório de {analista_sel}.")
  else:
    st.info("Nenhum dado encontrado no Firebase.")

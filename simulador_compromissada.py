import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(
    page_title="Simulador Compromissada",
    page_icon="💰",
    layout="wide",
)

# ── Estilo ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .metric-card {
        background: #f0f4ff;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
    }
    .highlight { color: #1a56db; font-weight: 700; }
    .sub-text  { color: #6b7280; font-size: 0.85rem; }
    div[data-testid="metric-container"] {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 12px 20px;
    }
</style>
""", unsafe_allow_html=True)

# ── Cabeçalho ────────────────────────────────────────────────────────────────
col_logo, col_title = st.columns([1, 9])
with col_logo:
    st.image("logo_conectar.png", width=90)
with col_title:
    st.title("Simulador de Compromissada")
st.caption(
    "Baseado na tabela XP · **Taxa Máx: 85% CDI** · **IR: 22,5%** · **Taxa de Consultoria: 0,5% a.a.**"
)
st.divider()

# ── Parâmetros ───────────────────────────────────────────────────────────────
TAXA_CDI_PRODUTO = 0.85       # 85% do CDI (Taxa Máx da tabela)
IR = 0.225                    # 22,5%
CONSULTORIA_AA = 0.005        # 0,5% ao ano
DIAS_UTEIS_ANO = 252

col_cdi, col_info = st.columns([1, 2])
with col_cdi:
    cdi_anual = st.number_input(
        "📊 Taxa CDI anual (%)",
        min_value=0.01, max_value=30.0,
        value=14.50, step=0.05, format="%.2f",
        help="Informe a taxa CDI vigente. Atualmente em torno de 14,50% a.a."
    )

with col_info:
    cdi_diario = (1 + cdi_anual / 100) ** (1 / DIAS_UTEIS_ANO) - 1
    taxa_diaria_produto = cdi_diario * TAXA_CDI_PRODUTO
    taxa_diaria_consultoria = CONSULTORIA_AA / DIAS_UTEIS_ANO

    st.markdown(f"""
    **Parâmetros calculados automaticamente:**
    - CDI diário efetivo: `{cdi_diario*100:.6f}%`
    - Rendimento bruto diário (85% CDI): `{taxa_diaria_produto*100:.6f}%`
    - Taxa de consultoria diária (0,5%/252): `{taxa_diaria_consultoria*100:.6f}%`
    """)

st.divider()

# ── Entradas diárias ─────────────────────────────────────────────────────────
st.subheader("📅 Valores investidos por dia")
st.markdown(
    '<p class="sub-text">Informe o saldo aplicado em compromissada em cada dia útil da semana.</p>',
    unsafe_allow_html=True,
)

DIAS = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"]
DEFAULT_VALUE = 100_000.0

cols = st.columns(5)
valores = {}
for dia, col in zip(DIAS, cols):
    with col:
        valores[dia] = st.number_input(
            dia,
            min_value=1_000.0,
            max_value=50_000_000.0,
            value=DEFAULT_VALUE,
            step=1_000.0,
            format="%.2f",
            key=f"valor_{dia}",
        )

st.divider()

# ── Cálculos ─────────────────────────────────────────────────────────────────
def calcular_dia(valor: float) -> dict:
    rendimento_bruto = valor * taxa_diaria_produto
    ir_reais = rendimento_bruto * IR
    rendimento_apos_ir = rendimento_bruto - ir_reais
    consultoria_reais = valor * taxa_diaria_consultoria
    rendimento_liquido = rendimento_apos_ir - consultoria_reais
    return {
        "Valor Investido": valor,
        "Rend. Bruto": rendimento_bruto,
        "IR (22,5%)": ir_reais,
        "Consultoria": consultoria_reais,
        "Rend. Líquido": rendimento_liquido,
    }

rows = []
for dia in DIAS:
    r = calcular_dia(valores[dia])
    r["Dia"] = dia
    rows.append(r)

df = pd.DataFrame(rows).set_index("Dia")
ordered_cols = ["Valor Investido", "Rend. Bruto", "IR (22,5%)", "Consultoria", "Rend. Líquido"]
df = df[ordered_cols]

# ── Métricas resumo ───────────────────────────────────────────────────────────
st.subheader("📈 Resumo da semana")

totais = df.sum()
m1, m2, m3, m4, m5 = st.columns(5)

m1.metric("💼 Total Investido", f"R$ {totais['Valor Investido']:,.2f}")
m2.metric("📊 Rend. Bruto Total", f"R$ {totais['Rend. Bruto']:,.2f}")
m3.metric("🏛️ IR Retido", f"R$ {totais['IR (22,5%)']:,.2f}")
m4.metric("🤝 Consultoria", f"R$ {totais['Consultoria']:,.2f}")
m5.metric(
    "✅ Rend. Líquido Total",
    f"R$ {totais['Rend. Líquido']:,.2f}",
    delta=f"{totais['Rend. Líquido'] / totais['Valor Investido'] * 100:.4f}% no período",
)

st.divider()

# ── Tabela detalhada ─────────────────────────────────────────────────────────
st.subheader("🗂️ Detalhamento por dia")

def fmt_brl(val):
    return f"R$ {val:,.2f}"

df_fmt = df.copy()
for col in ordered_cols:
    df_fmt[col] = df[col].apply(fmt_brl)

st.dataframe(
    df_fmt,
    use_container_width=True,
    height=245,
)

# ── Rodapé com totais na tabela ───────────────────────────────────────────────
totais_row = pd.DataFrame(
    [[fmt_brl(totais[c]) for c in ordered_cols]],
    columns=ordered_cols,
    index=["**TOTAL SEMANA**"],
)
st.dataframe(totais_row, use_container_width=True, height=80)


# ── Nota de rodapé ───────────────────────────────────────────────────────────
st.markdown("""
---
<p class="sub-text">
⚠️ Simulação baseada na taxa de 85% CDI (taxa máx. da tabela XP — Compromissada Liquidez Diária).
IR de 22,5% aplicado ao rendimento bruto (alíquota para aplicações de curto prazo até 180 dias).
Taxa de consultoria de 0,5% a.a. deduzida do rendimento após IR.
Valores estimados e não constituem garantia de retorno.
</p>
""", unsafe_allow_html=True)

import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.integrate import odeint

st.set_page_config(page_title="Laboratório de Cinética Prof", layout="wide")

# --- Lógica de Cálculo ---
def modelo_cinetico(y, t, k, na, nb, tipo):
    A = y[0]
    B = y[1] if tipo == "A + B → Produto" else 0
    velocidade = k * (A**na) * (B**nb if nb > 0 else 1)
    dAdt = -velocidade
    dPdt = velocidade
    return [dAdt, -velocidade, dPdt] if tipo == "A + B → Produto" else [dAdt, dPdt]

# --- Sidebar ---
st.sidebar.title("Configurações")
modelo = st.sidebar.radio("Tipo de Reação", ["A → Produto", "A + B → Produto"])
k = st.sidebar.slider("Constante k", 0.01, 2.0, 0.45)
a0 = st.sidebar.slider("[A]₀ Inicial", 0.1, 5.0, 2.0)
ordem_a = st.sidebar.slider("Ordem em A", 0, 2, 1)
t_max = st.sidebar.slider("Tempo Total", 10, 100, 50)

t = np.linspace(0, t_max, 1000)
if modelo == "A + B → Produto":
    b0 = st.sidebar.slider("[B]₀ Inicial", 0.1, 5.0, 2.0)
    ordem_b = st.sidebar.slider("Ordem em B", 0, 2, 2)
    sol = odeint(modelo_cinetico, [a0, b0, 0], t, args=(k, ordem_a, ordem_b, modelo))
    conc_a, conc_b, conc_p = sol[:, 0], sol[:, 1], sol[:, 2]
else:
    ordem_b = 0
    sol = odeint(modelo_cinetico, [a0, 0], t, args=(k, ordem_a, 0, modelo))
    conc_a, conc_p = sol[:, 0], sol[:, 1]
    conc_b = np.zeros_like(t)

st.sidebar.divider()
st.sidebar.subheader("🧮 Ferramentas")
modo_calc = st.sidebar.selectbox("O que calcular?", ["Nenhum", "Velocidade Média", "Velocidade Instantânea"])

reagente_alvo = "A"
if modo_calc != "Nenhum" and modelo == "A + B → Produto":
    reagente_alvo = st.sidebar.radio("Analisar qual?", ["A", "B"])

conc_alvo = conc_a if reagente_alvo == "A" else conc_b
ordem_alvo = ordem_a if reagente_alvo == "A" else ordem_b

# --- Gráfico Principal ---
st.title("🧪 Verificador de Velocidade Cinética")
col1, col2 = st.columns([2, 1])

fig = go.Figure()
fig.add_trace(go.Scatter(x=t, y=conc_a, name="[A]", line=dict(color='red', width=3)))
if modelo == "A + B → Produto":
    fig.add_trace(go.Scatter(x=t, y=conc_b, name="[B]", line=dict(color='green', width=3)))
fig.add_trace(go.Scatter(x=t, y=conc_p, name="[Produto]", line=dict(color='blue', width=3)))

# (Aqui entra a lógica das ferramentas que já tínhamos...)
# ... [Mantendo os cálculos de VM e VI conforme os códigos anteriores] ...

with col1:
    fig.update_layout(title="Concentração vs Tempo", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

# --- NOVO: Gráfico de Linearização (Abaixo do principal) ---
st.divider()
st.subheader(f"📈 Gráfico de Linearização para o Reagente {reagente_alvo}")

col_lin1, col_lin2 = st.columns([2, 1])

with col_lin1:
    fig_lin = go.Figure()
    if ordem_alvo == 0:
        y_lin = conc_alvo
        label_lin = f"[{reagente_alvo}]"
    elif ordem_alvo == 1:
        # Filtro para evitar log de zero
        y_lin = np.log(conc_alvo + 1e-9)
        label_lin = f"ln([{reagente_alvo}])"
    else:
        y_lin = 1 / (conc_alvo + 1e-9)
        label_lin = f"1 / [{reagente_alvo}]"
    
    fig_lin.add_trace(go.Scatter(x=t, y=y_lin, name="Linearização", line=dict(color='orange', width=2)))
    fig_lin.update_layout(height=350, xaxis_title="Tempo (s)", yaxis_title=label_lin, template="plotly_dark")
    st.plotly_chart(fig_lin, use_container_width=True)

with col_lin2:
    st.write(f"**Análise de Ordem {ordem_alvo}**")
    st.write(f"Este gráfico plota `{label_lin}` em função do tempo.")
    st.info("💡 Se a reação for realmente desta ordem, os pontos formarão uma linha reta!")
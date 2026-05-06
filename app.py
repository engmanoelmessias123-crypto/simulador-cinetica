import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.integrate import odeint

# Configuração da página
st.set_page_config(page_title="Laboratório de Cinética Prof", layout="wide")

# --- Lógica de Cálculo ---
def modelo_cinetico(y, t, k, na, nb, tipo):
    A = y[0]
    B = y[1] if tipo == "A + B → Produto" else 0
    velocidade = k * (A**na) * (B**nb if nb > 0 else 1)
    dAdt = -velocidade
    dPdt = velocidade
    return [dAdt, -velocidade, dPdt] if tipo == "A + B → Produto" else [dAdt, dPdt]

# --- Sidebar: Configurações ---
st.sidebar.title("Configurações")
modelo = st.sidebar.radio("Tipo de Reação", ["A → Produto", "A + B → Produto"], key="K1_MODELO")
k_sid = st.sidebar.slider("Constante k", 0.01, 2.0, 0.45, key="K2_K")
ordem_a_sid = st.sidebar.slider("Ordem em A", 0, 2, 1, key="K3_ORDEM_A")
a0_sid = st.sidebar.slider("[A]₀ Inicial", 0.1, 5.0, 2.0, key="K4_A0")
t_max = st.sidebar.slider("Tempo Total", 10, 100, 50, key="K5_TMAX")

# Resolução Cinética Principal
t = np.linspace(0, t_max, 1000)
if modelo == "A + B → Produto":
    b0_sid = st.sidebar.slider("[B]₀ Inicial", 0.1, 5.0, 2.0, key="K6_B0")
    ordem_b_sid = st.sidebar.slider("Ordem em B", 0, 2, 2, key="K7_ORDEM_B")
    sol = odeint(modelo_cinetico, [a0_sid, b0_sid, 0], t, args=(k_sid, ordem_a_sid, ordem_b_sid, modelo))
    conc_a, conc_b, conc_p = sol[:, 0], sol[:, 1], sol[:, 2]
else:
    sol = odeint(modelo_cinetico, [a0_sid, 0], t, args=(k_sid, ordem_a_sid, 0, modelo))
    conc_a, conc_p = sol[:, 0], sol[:, 1]
    conc_b = np.zeros_like(t)

# --- Opções de Exibição ---
st.sidebar.divider()
st.sidebar.subheader("👁️ Exibir no gráfico?")
mostrar_a = st.sidebar.checkbox("Reagente [A]", value=True, key="K8_VIEW_A")
mostrar_b = st.sidebar.checkbox("Reagente [B]", value=True, key="K9_VIEW_B") if modelo == "A + B → Produto" else False
mostrar_p = st.sidebar.checkbox("Produto", value=True, key="K10_VIEW_P")

# --- Ferramentas ---
st.sidebar.divider()
st.sidebar.subheader("🧮 Ferramentas")
modo_calc = st.sidebar.selectbox("O que calcular?", ["Nenhum", "Velocidade Média", "Velocidade Instantânea"], key="K11_SELECT_CALC")

reagente_alvo = "A"
if modo_calc != "Nenhum" and modelo == "A + B → Produto":
    reagente_alvo = st.sidebar.radio("Analisar qual?", ["A", "B"], key="K12_RADIO_ALVO")

conc_alvo = conc_a if reagente_alvo == "A" else conc_b
nome_alvo = f"[{reagente_alvo}]"
ordem_alvo = ordem_a_sid if reagente_alvo == "A" else (ordem_b_sid if modelo == "A + B → Produto" else 0)
mostrar_alvo = mostrar_a if reagente_alvo == "A" else mostrar_b

# --- 1. Gráfico Principal ---
st.title("🧪 Verificador de Velocidade Cinética")
col1, col2 = st.columns([2, 1])

fig_main = go.Figure()
if mostrar_a: fig_main.add_trace(go.Scatter(x=t, y=conc_a, name="[A]", line=dict(color='red', width=3)))
if mostrar_b and modelo == "A + B → Produto": fig_main.add_trace(go.Scatter(x=t, y=conc_b, name="[B]", line=dict(color='green', width=3)))
if mostrar_p: fig_main.add_trace(go.Scatter(x=t, y=conc_p, name="[Produto]", line=dict(color='blue', width=3)))

if modo_calc == "Velocidade Média":
    with col2:
        st.subheader(f"VM de {nome_alvo}")
        t1 = st.number_input("t1", 0.0, float(t_max), 5.0, key="K13_VM_T1")
        t2 = st.number_input("t2", 0.0, float(t_max), 15.0, key="K14_VM_T2")
        c1, c2 = np.interp(t1, t, conc_alvo), np.interp(t2, t, conc_alvo)
        if st.button("Revelar VM", key="K15_BTN_VM"):
            st.success(f"vm = {abs(c2-c1)/(t2-t1):.4f} M/s")
    if mostrar_alvo: fig_main.add_trace(go.Scatter(x=[t1, t2], y=[c1, c2], mode='markers+lines', name='Secante', line=dict(color='yellow', dash='dash')))

elif modo_calc == "Velocidade Instantânea":
    with col2:
        st.subheader(f"VI de {nome_alvo}")
        ti = st.slider("Instante (t)", 0.0, float(t_max), float(t_max/2), key="K16_VI_TI")
        ci = np.interp(ti, t, conc_alvo)
        if st.button("Revelar VI", key="K17_BTN_VI"):
            vi = k_sid * (np.interp(ti, t, conc_a)**ordem_a_sid) * (np.interp(ti, t, conc_b)**(ordem_b_sid if modelo == "A + B → Produto" else 0) if modelo == "A + B → Produto" else 1)
            st.success(f"v = {vi:.4f} M/s")

with col1:
    fig_main.update_layout(xaxis_title="Tempo (s)", yaxis_title="Molaridade (M)", template="plotly_dark")
    st.plotly_chart(fig_main, use_container_width=True, key="CHART_1_PRINCIPAL")

# --- 2. Linearização ---
st.divider()
st.subheader(f"📈 Linearização para {nome_alvo}")
c_l1, c_l2 = st.columns([2, 1])
with c_l1:
    if ordem_alvo == 0: y_lin, lab_lin = conc_alvo, nome_alvo
    elif ordem_alvo == 1: y_lin, lab_lin = np.log(conc_alvo + 1e-9), f"ln({nome_alvo})"
    else: y_lin, lab_lin = 1/(conc_alvo + 1e-9), f"1/{nome_alvo}"
    fig_lin = go.Figure(go.Scatter(x=t, y=y_lin, line=dict(color='orange', width=2)))
    fig_lin.update_layout(height=300, template="plotly_dark", yaxis_title=lab_lin)
    st.plotly_chart(fig_lin, use_container_width=True, key="CHART_2_LINEAR")

# --- 3. Comparador Histórico ---
st.divider()
st.header("📚 Comparador de Histórico")
if 'historico' not in st.session_state: st.session_state.historico = []

h1, h2, h3 = st.columns(3)
with h1: n_comp = st.number_input("Ordem", 0.0, 3.0, 1.0, step=0.5, key="K18_HIST_N")
with h2: c_comp = st.number_input("[A]₀", 0.1, 10.0, 2.0, key="K19_HIST_C")
with h3: k_comp = st.number_input("k", 0.01, 5.0, 0.45, key="K20_HIST_K")

bg, br = st.columns(2)
with bg:
    if st.button("🚀 Gravar Curva", key="K21_BTN_GRAVAR"):
        tc = np.linspace(0, t_max, 1000)
        sc = odeint(lambda y, t, k, n: [-k*(y[0]**n)], [c_comp], tc, args=(k_comp, n_comp))
        st.session_state.historico.append({'t': tc, 'y': sc[:, 0], 'label': f"Ordem {n_comp} | [A]₀ {c_comp}"})
with br:
    if st.button("🗑️ Resetar Histórico", key="K22_BTN_RESET"):
        st.session_state.historico = []
        st.rerun()

fig_h = go.Figure()
if not st.session_state.historico:
    fig_h.add_annotation(text="Adicione curvas para comparar", showarrow=False)
else:
    for c in st.session_state.historico:
        fig_h.add_trace(go.Scatter(x=c['t'], y=c['y'], name=c['label'], mode='lines'))

fig_h.update_layout(xaxis=dict(title="Tempo (s)", range=[0, 15]), yaxis=dict(title="Conc. [A]", range=[0, 6]), height=450, template="plotly_dark")
st.plotly_chart(fig_h, use_container_width=True, key="CHART_3_HISTORICO")

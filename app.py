import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.integrate import odeint

st.set_page_config(page_title="Laboratório de Cinética Prof", layout="wide")

# --- Ocultar o Menu e Toolbar ---
esconder_menu = """
    <style>
    #MainMenu {visibility: hidden !important;}
    header {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    .stApp [data-testid="stToolbar"] {display: none !important;}
    </style>
    """
st.markdown(esconder_menu, unsafe_allow_html=True)

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
modo_desafio = st.sidebar.toggle("🕵️ Modo Investigação", key="TOGGLE_DESAFIO")

if modo_desafio:
    if 'misterio_k' not in st.session_state:
        st.session_state.misterio_k = round(np.random.uniform(0.1, 1.5), 2)
        st.session_state.misterio_ordem = int(np.random.choice([0, 1, 2]))
    st.sidebar.success("**Modo Ativado!**\nDescubra a Ordem e o 'k' desta substância.")
    if st.sidebar.button("🔄 Gerar Nova Substância"):
        st.session_state.misterio_k = round(np.random.uniform(0.1, 1.5), 2)
        st.session_state.misterio_ordem = int(np.random.choice([0, 1, 2]))
        st.rerun()
    modelo, k_sid, ordem_a_sid = "A → Produto", st.session_state.misterio_k, st.session_state.misterio_ordem
    a0_sid = st.sidebar.slider("[A]₀ Inicial", 0.1, 5.0, 2.0, key="K4_A0_DES")
    t_max = st.sidebar.slider("Tempo Total", 10, 100, 50, key="K5_TMAX_DES")
else:
    modelo = st.sidebar.radio("Tipo de Reação", ["A → Produto", "A + B → Produto"], key="K1_MODELO")
    k_sid = st.sidebar.slider("Constante k", 0.01, 2.0, 0.45, key="K2_K")
    ordem_a_sid = st.sidebar.slider("Ordem em A", 0, 2, 1, key="K3_ORDEM_A")
    a0_sid = st.sidebar.slider("[A]₀ Inicial", 0.1, 5.0, 2.0, key="K4_A0")
    t_max = st.sidebar.slider("Tempo Total", 10, 100, 50, key="K5_TMAX")

t = np.linspace(0, t_max, 1000)
if modelo == "A + B → Produto":
    b0_sid = st.sidebar.slider("[B]₀ Inicial", 0.1, 5.0, 2.0, key="K6_B0")
    ordem_b_sid = st.sidebar.slider("Ordem em B", 0, 2, 2, key="K7_ORDEM_B")
    sol = odeint(modelo_cinetico, [a0_sid, b0_sid, 0], t, args=(k_sid, ordem_a_sid, ordem_b_sid, modelo))
    conc_a, conc_b, conc_p = sol[:, 0], sol[:, 1], sol[:, 2]
else:
    sol = odeint(modelo_cinetico, [a0_sid, 0], t, args=(k_sid, ordem_a_sid, 0, modelo))
    conc_a, conc_p, conc_b = sol[:, 0], sol[:, 1], np.zeros_like(t)

# --- TRAVA DA REALIDADE FÍSICA ---
limite_zero = 1e-5
indices_validos = (conc_a > limite_zero) & (conc_b > limite_zero if modelo == "A + B → Produto" else True)
t, conc_a, conc_p = t[indices_validos], conc_a[indices_validos], conc_p[indices_validos]
if modelo == "A + B → Produto": conc_b = conc_b[indices_validos]

# --- Opções de Exibição ---
st.sidebar.divider()
mostrar_a = st.sidebar.checkbox("Reagente [A]", value=True, key="K8_VIEW_A")
mostrar_b = st.sidebar.checkbox("Reagente [B]", value=True, key="K9_VIEW_B") if modelo == "A + B → Produto" else False
mostrar_p = st.sidebar.checkbox("Produto", value=True, key="K10_VIEW_P")
mostrar_meia_vida = st.sidebar.checkbox("⏱️ Meia-Vida (t½)", value=False, key="VIEW_MEIA_VIDA") if modelo == "A → Produto" else False

st.sidebar.divider()
modo_calc = st.sidebar.selectbox("O que calcular?", ["Nenhum", "Velocidade Média", "Velocidade Instantânea"], key="K11_SELECT_CALC")
reagente_alvo = st.sidebar.radio("Analisar qual?", ["A", "B"], key="K12_RADIO_ALVO") if modo_calc != "Nenhum" and modelo == "A + B → Produto" else "A"
conc_alvo, nome_alvo = (conc_a, f"[{reagente_alvo}]") if reagente_alvo == "A" else (conc_b, f"[{reagente_alvo}]")

# --- 1. Gráfico Principal ---
st.title("🧪 Simulação da Velocidade da Reação")
col1, col2 = st.columns([2, 1])
fig_main = go.Figure()
if mostrar_a: fig_main.add_trace(go.Scatter(x=t, y=conc_a, name="[A]", line=dict(color='red', width=3)))
if mostrar_b: fig_main.add_trace(go.Scatter(x=t, y=conc_b, name="[B]", line=dict(color='green', width=3)))
if mostrar_p: fig_main.add_trace(go.Scatter(x=t, y=conc_p, name="[Produto]", line=dict(color='blue', width=3)))

if mostrar_meia_vida and modelo == "A → Produto":
    c_at, t_at = a0_sid, 0.0
    for i in range(1, 5):
        t_m = c_at/(2*k_sid) if ordem_a_sid==0 else (np.log(2)/k_sid if ordem_a_sid==1 else 1/(k_sid*c_at))
        t_at += t_m
        c_at /= 2
        if t_at > t[-1]: break
        fig_main.add_shape(type="line", x0=t_at, x1=t_at, y0=0, y1=c_at, line=dict(color="orange", width=1, dash="dot"))
        fig_main.add_shape(type="line", x0=0, x1=t_at, y0=c_at, y1=c_at, line=dict(color="orange", width=1, dash="dot"))

# --- Ferramentas Lateral ---
with col2:
    t_lim = float(t[-1])
    if modo_calc == "Velocidade Média":
        t1 = st.number_input("Escolha t1", 0.0, t_lim, min(1.0, t_lim/4), key="VM_T1")
        t2 = st.number_input("Escolha t2", 0.0, t_lim, min(5.0, t_lim/2), key="VM_T2")
        c1, c2 = np.interp(t1, t, conc_alvo), np.interp(t2, t, conc_alvo)
        v_m = abs(c2 - c1) / (t2 - t1) if t2 != t1 else 0
        st.latex(rf"v_m = \left| \frac{{\Delta {nome_alvo}}}{{\Delta t}} \right|")
        if st.button("Revelar Velocidade Média"): st.success(f"Resposta: {v_m:.4f} M/s")
        fig_main.add_trace(go.Scatter(x=[t1, t2], y=[c1, c2], mode='markers+lines+text', name='Secante', text=[f"{c1:.2f}M", f"{c2:.2f}M"], line=dict(color='yellow', dash='dash')))

    elif modo_calc == "Velocidade Instantânea":
        ti = st.slider("Escolha o instante (t)", 0.0, t_lim, t_lim/2)
        ci = np.interp(ti, t, conc_alvo)
        vi = k_sid * (np.interp(ti, t, conc_a)**ordem_a_sid) * (np.interp(ti,

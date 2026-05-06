import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.integrate import odeint

st.set_page_config(page_title="Simulador de Cinética Avançado", layout="wide")

# --- Ocultar o Menu ---
esconder_menu = """
    <style>
    #MainMenu {visibility: hidden !important;}
    header {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    .stApp [data-testid="stToolbar"] {display: none !important;}
    </style>
    """
st.markdown(esconder_menu, unsafe_allow_html=True)

# --- Lógica de Cálculo (Com Coeficientes Estequiométricos) ---
def modelo_cinetico(y, t, k, na, nb, coef_a, coef_b, tipo):
    A = max(0, y[0])
    B = max(0, y[1]) if tipo == "A + B → Produto" else 0
    
    # Lei de velocidade fenomenológica
    v_reacao = k * (A**na) * (B**nb if nb > 0 else 1)
    
    # Derivadas baseadas na estequiometria: dC/dt = -coef * v
    dAdt = -coef_a * v_reacao
    dBdt = -coef_b * v_reacao if tipo == "A + B → Produto" else 0
    dPdt = 1 * v_reacao # Produto formado
    
    return [dAdt, dBdt, dPdt] if tipo == "A + B → Produto" else [dAdt, dPdt]

# --- Sidebar: Configurações ---
st.sidebar.title("⚙️ Parâmetros Reacionais")

modelo = st.sidebar.radio("Modelo", ["A → Produto", "A + B → Produto"], key="K1_MODELO")

with st.sidebar.expander("🌡️ Termodinâmica (Arrhenius)", expanded=True):
    temp = st.slider("Temperatura (K)", 273, 500, 300, key="K_TEMP")
    ea = st.number_input("Energia de Ativação (J/mol)", value=50000.0, step=1000.0)
    a_pre = 1e8 # Fator de frequência fixo
    r_gas = 8.314
    # Cálculo automático do k
    k_arrhenius = a_pre * np.exp(-ea / (r_gas * temp))
    st.info(f"**k calculado:** {k_arrhenius:.4e}")

with st.sidebar.expander("🧪 Estequiometria e Ordens"):
    coef_a = st.number_input("Coeficiente de A", 1, 5, 1)
    ordem_a = st.slider("Ordem em A", 0.0, 2.0, 1.0, 0.5)
    
    coef_b, ordem_b = 0, 0
    if modelo == "A + B → Produto":
        coef_b = st.number_input("Coeficiente de B", 1, 5, 1)
        ordem_b = st.slider("Ordem em B", 0.0, 2.0, 1.0, 0.5)

a0 = st.sidebar.slider("[A]₀ Inicial", 0.1, 5.0, 2.0)
t_max = st.sidebar.slider("Tempo Total (s)", 10, 200, 50)

# --- Integração Numérica ---
t_vetor = np.linspace(0, t_max, 1000)
if modelo == "A + B → Produto":
    b0 = st.sidebar.slider("[B]₀ Inicial", 0.1, 5.0, 2.0)
    sol = odeint(modelo_cinetico, [a0, b0, 0], t_vetor, args=(k_arrhenius, ordem_a, ordem_b, coef_a, coef_b, modelo))
    conc_a, conc_b, conc_p = sol[:, 0], sol[:, 1], sol[:, 2]
else:
    sol = odeint(modelo_cinetico, [a0, 0], t_vetor, args=(k_arrhenius, ordem_a, 0, coef_a, 0, modelo))
    conc_a, conc_p = sol[:, 0], sol[:, 1]
    conc_b = np.zeros_like(t_vetor)

# --- Interface Principal ---
st.title("🧪 Simulador de Engenharia Química")
st.write(f"Simulando: **{coef_a if coef_a > 1 else ''}A {f'+ {coef_b if coef_b > 1 else ''}B' if modelo == 'A + B → Produto' else ''} → Produto**")

col1, col2 = st.columns([2, 1])

# --- Gráfico Principal ---
fig_main = go.Figure()
fig_main.add_trace(go.Scatter(x=t_vetor, y=conc_a, name="[A]", line=dict(color='red', width=3)))
if modelo == "A + B → Produto":
    fig_main.add_trace(go.Scatter(x=t_vetor, y=conc_b, name="[B]", line=dict(color='green', width=3)))
fig_main.add_trace(go.Scatter(x=t_vetor, y=conc_p, name="[Produto]", line=dict(color='blue', width=3)))

# --- Ferramenta de Velocidade Média ---
st.sidebar.divider()
modo_calc = st.sidebar.selectbox("Análise Extra", ["Nenhum", "Velocidade Média"])

if modo_calc == "Velocidade Média":
    with col2:
        st.subheader("📊 Velocidade Média")
        t1 = st.number_input("t1 (s)", 0.0, float(t_max), min(5.0, float(t_max)), key="VM_T1")
        t2 = st.number_input("t2 (s)", 0.0, float(t_max), min(20.0, float(t_max)), key="VM_T2")
        
        c1 = np.interp(t1, t_vetor, conc_a)
        c2 = np.interp(t2, t_vetor, conc_a)
        
        v_m = abs(c2 - c1) / (t2 - t1) if t2 != t1 else 0
        st.metric("VM de [A]", f"{v_m:.4f} M/s")
        
        fig_main.add_trace(go.Scatter(x=[t1, t2], y=[c1, c2], mode='markers+lines', name='Secante', line=dict(color='yellow', dash='dash')))

with col1:
    fig_main.update_layout(template="plotly_dark", xaxis_title="Tempo (s)", yaxis_title="Concentração (M)")
    st.plotly_chart(fig_main, use_container_width=True)

# --- Linearização Dinâmica ---
st.divider()
st.subheader("📈 Análise de Dados (Linearização)")
cl_1, cl_2 = st.columns([2, 1])

# Define Y com base na ordem de A
if ordem_a == 0: y_lin, lab_lin = conc_a, "[A]"
elif ordem_a == 1: y_lin, lab_lin = np.log(conc_a + 1e-9), "ln([A])"
else: y_lin, lab_lin = 1/(conc_a + 1e-9), "1/[A]"

fig_lin = go.Figure(go.Scatter(x=t_vetor, y=y_lin, name="Dados", line=dict(color='orange')))

with cl_2:
    st.write("Verifique a linearidade para confirmar a ordem:")
    t1_l = st.number_input("t1", 0.0, float(t_max), min(5.0, float(t_max)), key="L_T1")
    t2_l = st.number_input("t2", 0.0, float(t_max), min(25.0, float(t_max)), key="L_T2")
    y1_l = np.interp(t1_l, t_vetor, y_lin)
    y2_l = np.interp(t2_l, t_vetor, y_lin)
    m = (y2_l - y1_l)/(t2_l - t1_l) if t2_l != t1_l else 0
    st.info(f"Inclinação (m): {m:.4f}")

with cl_1:
    fig_lin.update_layout(template="plotly_dark", height=300, yaxis_title=lab_lin)
    st.plotly_chart(fig_lin, use_container_width=True)

# --- Comparador de Memória ---
st.divider()
st.subheader("💾 Comparador Histórico")
if 'historico' not in st.session_state: st.session_state.historico = []

if st.button("Gravar Curva Atual"):
    label = f"T={temp}K | Ea={ea/1000}kJ | n={ordem_a}"
    st.session_state.historico.append({'x': t_vetor, 'y': conc_a, 'lab': label})

fig_h = go.Figure()
for h in st.session_state.historico:
    fig_h.add_trace(go.Scatter(x=h['x'], y=h['y'], name=h['lab']))
fig_h.update_layout(template="plotly_dark", title="Comparação de [A]")
st.plotly_chart(fig_h, use_container_width=True)

if st.button("Limpar Histórico"):
    st.session_state.historico = []
    st.rerun()
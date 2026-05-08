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

# ------------------------------------------------------
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
        
    modelo = "A → Produto"
    k_sid = st.session_state.misterio_k
    ordem_a_sid = st.session_state.misterio_ordem
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
    conc_a, conc_p = sol[:, 0], sol[:, 1]
    conc_b = np.zeros_like(t)

# --- TRAVA DA REALIDADE FÍSICA ---
limite_zero = 1e-5
indices_validos = (conc_a > limite_zero) & (conc_b > limite_zero if modelo == "A + B → Produto" else True)
t = t[indices_validos]
conc_a, conc_p = conc_a[indices_validos], conc_p[indices_validos]
if modelo == "A + B → Produto": conc_b = conc_b[indices_validos]

# --- Opções de Exibição ---
st.sidebar.divider()
mostrar_a = st.sidebar.checkbox("Reagente [A]", value=True, key="K8_VIEW_A")
mostrar_b = st.sidebar.checkbox("Reagente [B]", value=True, key="K9_VIEW_B") if modelo == "A + B → Produto" else False
mostrar_p = st.sidebar.checkbox("Produto", value=True, key="K10_VIEW_P")
mostrar_meia_vida = st.sidebar.checkbox("⏱️ Meia-Vida (t½)", value=False, key="VIEW_MEIA_VIDA") if modelo == "A → Produto" else False

# --- Ferramentas ---
st.sidebar.divider()
modo_calc = st.sidebar.selectbox("O que calcular?", ["Nenhum", "Velocidade Média", "Velocidade Instantânea"], key="K11_SELECT_CALC")

reagente_alvo = "A"
if modo_calc != "Nenhum" and modelo == "A + B → Produto":
    reagente_alvo = st.sidebar.radio("Analisar qual?", ["A", "B"], key="K12_RADIO_ALVO")

conc_alvo = conc_a if reagente_alvo == "A" else conc_b
nome_alvo = f"[{reagente_alvo}]"
ordem_alvo = ordem_a_sid if reagente_alvo == "A" else (ordem_b_sid if modelo == "A + B → Produto" else 0)

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
        if ordem_a_sid == 0: t_m = c_at/(2*k_sid)
        elif ordem_a_sid == 1: t_m = np.log(2)/k_sid
        else: t_m = 1/(k_sid*c_at)
        t_at += t_m
        c_at /= 2
        if t_at > t[-1]: break
        fig_main.add_shape(type="line", x0=t_at, x1=t_at, y0=0, y1=c_at, line=dict(color="orange", width=1, dash="dot"))
        fig_main.add_shape(type="line", x0=0, x1=t_at, y0=c_at, y1=c_at, line=dict(color="orange", width=1, dash="dot"))

# --- Cálculos Lateral ---
with col2:
    t_limite = float(t[-1])
    if modo_calc == "Velocidade Média":
        t1 = st.number_input("Escolha t1", 0.0, t_limite, min(1.0, t_limite/4), key="VM_T1")
        t2 = st.number_input("Escolha t2", 0.0, t_limite, min(5.0, t_limite/2), key="VM_T2")
        c1, c2 = np.interp(t1, t, conc_alvo), np.interp(t2, t, conc_alvo)
        v_m = abs(c2 - c1) / (t2 - t1) if t2 != t1 else 0
        if st.button("Revelar Velocidade Média"): st.success(f"{v_m:.4f} M/s")
        fig_main.add_trace(go.Scatter(x=[t1, t2], y=[c1, c2], mode='markers+lines', name='Secante', line=dict(color='yellow', dash='dash')))

    elif modo_calc == "Velocidade Instantânea":
        ti = st.slider("Escolha o instante (t)", 0.0, t_limite, t_limite/2, key="K16_VI_TI")
        ci = np.interp(ti, t, conc_alvo)
        vi = k_sid * (np.interp(ti, t, conc_a)**ordem_a_sid) * (np.interp(ti, t, conc_b)**ordem_b_sid if modelo == "A + B → Produto" else 1)
        slope = -vi
        b_c = ci - slope * ti
        t_int_x = -b_c / slope if slope != 0 else t_max
        t_s, t_e = 0.0, float(t_int_x)
        c_s, c_e = b_c, 0.0
        if st.button("Revelar Velocidade"): st.success(f"{vi:.4f} M/s")
        if st.button("📥 Salvar Ponto da Tangente"):
            if 'pontos_taxa' not in st.session_state: st.session_state.pontos_taxa = []
            st.session_state.pontos_taxa.append({'[C]': float(ci), 'Velocidade': float(vi)})
        fig_main.add_trace(go.Scatter(x=[t_s, t_e], y=[c_s, c_e], mode='lines', name='Tangente', line=dict(color='cyan')))

with col1:
    fig_main.update_layout(xaxis_title="Tempo (s)", yaxis_title="Molaridade (M)", template="plotly_dark")
    st.plotly_chart(fig_main, use_container_width=True)

# =====================================================================
# --- BLOCO CORRIGIDO: MÉTODO DIFERENCIAL ---
# =====================================================================
st.divider()
st.header("🔬 Método Diferencial: Velocidade vs Concentração")
c_t1, c_t2 = st.columns([2, 1])

with c_t2:
    st.write("### Coleta de Dados")
    linearizar_dif = st.checkbox("Plotar ln(v) vs ln[C] para achar a Ordem", key="CHK_LOG_LOG")
    mostrar_tendencia = st.checkbox("📈 Traçar Linha de Tendência", key="CHK_TENDENCIA")
    if st.button("🗑️ Limpar Pontos Coletados"):
        st.session_state.pontos_taxa = []
        st.rerun()
    if 'pontos_taxa' in st.session_state and len(st.session_state.pontos_taxa) > 0:
        st.dataframe(st.session_state.pontos_taxa, hide_index=True)

with c_t1:
    fig_taxa = go.Figure()
    if 'pontos_taxa' in st.session_state and len(st.session_state.pontos_taxa) > 0:
        c_vals = np.array([p['[C]'] for p in st.session_state.pontos_taxa])
        v_vals = np.array([p['Velocidade'] for p in st.session_state.pontos_taxa])
        
        # Definição segura para evitar NameError
        log_c = np.log(c_vals + 1e-9)
        log_v = np.log(v_vals + 1e-9)

        if linearizar_dif:
            fig_taxa.add_trace(go.Scatter(x=log_c, y=log_v, mode='markers', name='Medições', marker=dict(color='cyan', size=10)))
            fig_taxa.update_layout(xaxis_title=f"ln({nome_alvo})", yaxis_title="ln(v)")
            if mostrar_tendencia and len(set(log_c)) > 1:
                try:
                    z = np.polyfit(log_c, log_v, 1)
                    p = np.poly1d(z)
                    x_r = np.linspace(min(log_c), max(log_c), 100)
                    fig_taxa.add_trace(go.Scatter(x=x_r, y=p(x_r), mode='lines', name=f'Ajuste (m={z[0]:.2f})', line=dict(color='yellow', dash='dash')))
                except: pass
        else:
            fig_taxa.add_trace(go.Scatter(x=c_vals, y=v_vals, mode='markers', name='Medições', marker=dict(color='magenta', size=12, symbol='x')))
            fig_taxa.update_layout(xaxis_title=f"Concentração {nome_alvo} (M)", yaxis_title="Velocidade (M/s)")
            if mostrar_tendencia and len(set(c_vals)) > 1:
                try:
                    z = np.polyfit(log_c, log_v, 1)
                    n_fit, k_fit = z[0], np.exp(z[1])
                    c_s = np.linspace(min(c_vals), max(c_vals), 100)
                    v_s = k_fit * (c_s**n_fit)
                    fig_taxa.add_trace(go.Scatter(x=c_s, y=v_s, mode='lines', name='Curva Ajuste', line=dict(color='yellow', dash='dash')))
                except: pass
    else:
        fig_taxa.add_annotation(text="Salve pontos da tangente acima!", showarrow=False)

    fig_taxa.update_layout(template="plotly_dark", height=400)
    st.plotly_chart(fig_taxa, use_container_width=True)

# --- 2. Linearização ---
st.divider()
st.subheader(f"📈 Linearização para {nome_alvo}")
c_l1, c_l2 = st.columns([2, 1])

if ordem_alvo == 0: y_lin, lab_lin = conc_alvo, nome_alvo
elif ordem_alvo == 1: y_lin, lab_lin = np.log(conc_alvo + 1e-9), f"ln({nome_alvo})"
else: y_lin, lab_lin = 1/(conc_alvo + 1e-9), f"1/{nome_alvo}"

with c_l2:
    t_r_max = float(t[-1])
    t1_l = st.number_input("Escolha t1", 0.0, t_r_max, min(1.0, t_r_max/4), key="L1")
    t2_l = st.number_input("Escolha t2", 0.0, t_r_max, min(5.0, t_r_max/2), key="L2")
    y1_l, y2_l = np.interp(t1_l, t, y_lin), np.interp(t2_l, t, y_lin)
    m_l = (y2_l - y1_l) / (t2_l - t1_l) if t2_l != t1_l else 0
    k_calc = -m_l if ordem_alvo <= 1 else m_l
    if st.button("Calcular k"): st.success(f"k calculado: {k_calc:.4f}")

with c_l1:
    fig_lin = go.Figure(go.Scatter(x=t, y=y_lin, name="Reta", line=dict(color='orange')))
    fig_lin.add_trace(go.Scatter(x=[t1_l, t2_l], y=[y1_l, y2_l], mode='markers', marker=dict(color='white', symbol='x')))
    fig_lin.update_layout(template="plotly_dark", height=350, yaxis_title=lab_lin)
    st.plotly_chart(fig_lin, use_container_width=True)

# --- 3. Histórico ---
st.divider()
st.header("📚 Comparador de Curvas")
if 'historico' not in st.session_state: st.session_state.historico = []
h1, h2, h3 = st.columns(3)
n_c = h1.number_input("Ordem", 0.0, 3.0, 1.0, step=0.5)
c_c = h2.number_input("[A]₀", 0.1, 10.0, 2.0)
k_c = h3.number_input("k", 0.01, 5.0, 0.45)

if st.button("🚀 Gravar Curva"):
    tc = np.linspace(0, t_max, 1000)
    sc = odeint(lambda y, t, k, n: [-k*(y[0]**n)], [c_c], tc, args=(k_c, n_c))
    st.session_state.historico.append({'t': tc, 'y': sc[:,0], 'lab': f"n:{n_c}|k:{k_c}"})
if st.button("🗑️ Resetar"): st.session_state.historico = []; st.rerun()

fig_h = go.Figure()
for c in st.session_state.historico: fig_h.add_trace(go.Scatter(x=c['t'], y=c['y'], name=c['lab']))
fig_h.update_layout(template="plotly_dark", height=400, xaxis_title="Tempo (s)", yaxis_title="Conc.")
st.plotly_chart(fig_h, use_container_width=True)

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
        vi = k_sid * (np.interp(ti, t, conc_a)**ordem_a_sid) * (np.interp(ti, t, conc_b)**(ordem_b_sid if modelo=="A+B → Produto" else 0) if modelo=="A+B → Produto" else 1)
        slope, b_c = -vi, ci - (-vi * ti)
        t_int_x = -b_c/slope if slope != 0 else t_max
        st.info(f"**Dados da Tangente:**\n\n$\Delta {nome_alvo} = {-b_c:.3f}$ M\n\n$\Delta t = {t_int_x:.3f}$ s")
        if st.button("Revelar Velocidade"): st.success(f"Velocidade: {vi:.4f} M/s")
        if st.button("📥 Salvar Ponto"):
            if 'pontos_taxa' not in st.session_state: st.session_state.pontos_taxa = []
            st.session_state.pontos_taxa.append({'[C]': float(ci), 'Velocidade': float(vi)})
        fig_main.add_trace(go.Scatter(x=[0, t_int_x], y=[b_c, 0], mode='lines', name='Tangente', line=dict(color='cyan', width=2)))
        fig_main.add_trace(go.Scatter(x=[0, t_int_x], y=[b_c, 0], mode='markers+text', text=[f"(0, {b_c:.2f})", f"({t_int_x:.2f}, 0)"], marker=dict(color='yellow', symbol='x')))
        fig_main.add_trace(go.Scatter(x=[0, 0, t_int_x], y=[0, b_c, 0], mode='lines', showlegend=False, line=dict(color='cyan', dash='dot')))

with col1:
    fig_main.update_layout(xaxis_title="Tempo (s)", yaxis_title="Molaridade (M)", template="plotly_dark")
    st.plotly_chart(fig_main, use_container_width=True)

# --- Método Diferencial ---
st.divider()
st.header("🔬 Método Diferencial: Velocidade vs Concentração")
c_t1, c_t2 = st.columns([2, 1])
with c_t2:
    linearizar_dif = st.checkbox("Plotar ln(v) vs ln[C]", key="CHK_LOG_LOG")
    mostrar_tendencia = st.checkbox("📈 Linha de Tendência", key="CHK_TENDENCIA")
    if st.button("🗑️ Limpar"): st.session_state.pontos_taxa = []; st.rerun()
    if 'pontos_taxa' in st.session_state and st.session_state.pontos_taxa: st.dataframe(st.session_state.pontos_taxa)

with c_t1:
    fig_taxa = go.Figure()
    if 'pontos_taxa' in st.session_state and st.session_state.pontos_taxa:
        c_vals, v_vals = np.array([p['[C]'] for p in st.session_state.pontos_taxa]), np.array([p['Velocidade'] for p in st.session_state.pontos_taxa])
        lc, lv = np.log(c_vals + 1e-9), np.log(v_vals + 1e-9)
        if linearizar_dif:
            fig_taxa.add_trace(go.Scatter(x=lc, y=lv, mode='markers', name='Dados'))
            if mostrar_tendencia and len(set(lc)) > 1:
                z = np.polyfit(lc, lv, 1)
                fig_taxa.add_trace(go.Scatter(x=lc, y=np.poly1d(z)(lc), mode='lines', name=f'm={z[0]:.2f}', line=dict(color='yellow', dash='dash')))
        else:
            fig_taxa.add_trace(go.Scatter(x=c_vals, y=v_vals, mode='markers', name='Medições'))
            if mostrar_tendencia and len(set(c_vals)) > 1:
                z = np.polyfit(lc, lv, 1)
                cs = np.linspace(min(c_vals), max(c_vals), 100)
                fig_taxa.add_trace(go.Scatter(x=cs, y=np.exp(z[1])*(cs**z[0]), mode='lines', name='Ajuste', line=dict(color='yellow', dash='dash')))
    fig_taxa.update_layout(template="plotly_dark", height=400)
    st.plotly_chart(fig_taxa, use_container_width=True)

# --- Linearização e Histórico ---
st.divider()
st.subheader(f"📈 Linearização para {nome_alvo}")
c_l1, c_l2 = st.columns([2, 1])
y_lin, lab_lin = (conc_alvo, nome_alvo) if ordem_a_sid==0 else ((np.log(conc_alvo+1e-9), f"ln{nome_alvo}") if ordem_a_sid==1 else (1/(conc_alvo+1e-9), f"1/{nome_alvo}"))
with c_l2:
    t1_l = st.number_input("t1", 0.0, float(t[-1]), float(t[-1]/4), key="l1")
    t2_l = st.number_input("t2", 0.0, float(t[-1]), float(t[-1]/2), key="l2")
    m_l = (np.interp(t2_l, t, y_lin) - np.interp(t1_l, t, y_lin)) / (t2_l - t1_l) if t2_l != t1_l else 0
    if st.button("Calcular k"): st.success(f"k: {abs(m_l):.4f}")
with c_l1:
    fig_lin = go.Figure(go.Scatter(x=t, y=y_lin, line=dict(color='orange')))
    fig_lin.update_layout(template="plotly_dark", height=350, yaxis_title=lab_lin)
    st.plotly_chart(fig_lin, use_container_width=True)

st.divider()
st.header("📚 Comparador")
if 'historico' not in st.session_state: st.session_state.historico = []
h1, h2, h3 = st.columns(3)
nc, cc, kc = h1.number_input("Ordem", 0.0, 3.0, 1.0), h2.number_input("[A]₀", 0.1, 10.0, 2.0), h3.number_input("k", 0.01, 5.0, 0.45)
if st.button("🚀 Gravar"):
    tc = np.linspace(0, t_max, 1000)
    st.session_state.historico.append({'t': tc, 'y': odeint(lambda y,t,k,n: [-k*(y[0]**n)], [cc], tc, args=(kc, nc))[:,0], 'lab': f"n:{nc}|k:{kc}"})
fig_h = go.Figure()
for c in st.session_state.historico: fig_h.add_trace(go.Scatter(x=c['t'], y=c['y'], name=c['lab']))
fig_h.update_layout(template="plotly_dark", height=400)
st.plotly_chart(fig_h, use_container_width=True)

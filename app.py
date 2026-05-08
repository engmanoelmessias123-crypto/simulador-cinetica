import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.integrate import odeint

st.set_page_config(page_title="Laboratório de Cinética Prof", layout="wide")

# --- NOVO BLOCO: Ocultar o Menu (Versão Definitiva) ---
esconder_menu = """
    <style>
    #MainMenu {visibility: hidden !important;}
    header {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    .stApp [data-testid="stToolbar"] {display: none !important;}
    [data-testid="stHeaderActionElements"] {display: none !important;}
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
    
    st.sidebar.success("**Modo Ativado!**\nVá na aba de Linearização e descubra a Ordem e a constante 'k' desta substância.")
    
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

# --- TRAVA MATEMÁTICA DA REALIDADE FÍSICA ---
limite_zero = 1e-5
indices_validos = (conc_a > limite_zero) & (conc_b > limite_zero if modelo == "A + B → Produto" else True)
t = t[indices_validos]
conc_a = conc_a[indices_validos]
conc_p = conc_p[indices_validos]
if modelo == "A + B → Produto": conc_b = conc_b[indices_validos]

# --- Opções de Exibição ---
st.sidebar.divider()
st.sidebar.subheader("👁️ Exibir no gráfico?")
mostrar_a = st.sidebar.checkbox("Reagente [A]", value=True, key="K8_VIEW_A")
mostrar_b = st.sidebar.checkbox("Reagente [B]", value=True, key="K9_VIEW_B") if modelo == "A + B → Produto" else False
mostrar_p = st.sidebar.checkbox("Produto", value=True, key="K10_VIEW_P")
mostrar_meia_vida = st.sidebar.checkbox("⏱️ Meia-Vida (t½)", value=False, key="VIEW_MEIA_VIDA") if modelo == "A → Produto" else False

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
st.title("🧪 Simulação da Velocidade da Reação")
col1, col2 = st.columns([2, 1])

fig_main = go.Figure()
if mostrar_a: fig_main.add_trace(go.Scatter(x=t, y=conc_a, name="[A]", line=dict(color='red', width=3)))
if mostrar_b and modelo == "A + B → Produto": fig_main.add_trace(go.Scatter(x=t, y=conc_b, name="[B]", line=dict(color='green', width=3)))
if mostrar_p: fig_main.add_trace(go.Scatter(x=t, y=conc_p, name="[Produto]", line=dict(color='blue', width=3)))

if mostrar_meia_vida and modelo == "A → Produto":
    c_atual, t_atual = a0_sid, 0.0
    for i in range(1, 5): 
        if ordem_a_sid == 0: t_meia = c_atual / (2 * k_sid)
        elif ordem_a_sid == 1: t_meia = np.log(2) / k_sid
        else: t_meia = 1 / (k_sid * c_atual)
        t_atual += t_meia
        c_atual /= 2
        if t_atual > t[-1]: break
        fig_main.add_shape(type="line", x0=t_atual, x1=t_atual, y0=0, y1=c_atual, line=dict(color="orange", width=1, dash="dot"))
        fig_main.add_shape(type="line", x0=0, x1=t_atual, y0=c_atual, y1=c_atual, line=dict(color="orange", width=1, dash="dot"))
        fig_main.add_trace(go.Scatter(x=[t_atual], y=[c_atual], mode='markers+text', name=f'{i}º t½', text=[f"{t_atual:.1f}s"], textposition="top right", marker=dict(color='orange', symbol='diamond')))

# --- Cálculos Lateral ---
with col2:
    t_limite = float(t[-1])
    if modo_calc == "Velocidade Média":
        st.subheader(f"Cálculo da Velocidade Média de {nome_alvo}")
        t1 = st.number_input("Escolha t1", 0.0, t_limite, min(1.0, t_limite/4), key="VM_T1")
        t2 = st.number_input("Escolha t2", 0.0, t_limite, min(5.0, t_limite/2), key="VM_T2")
        c1, c2 = np.interp(t1, t, conc_alvo), np.interp(t2, t, conc_alvo)
        v_media = abs(c2 - c1) / (t2 - t1) if t2 != t1 else 0
        st.latex(rf"v_m = \left| \frac{{\Delta {nome_alvo}}}{{\Delta t}} \right|")
        if st.button("Revelar Velocidade Média", key="K15_BTN_VM"):
            st.latex(rf"v_m = \frac{{|{c2:.3f} - {c1:.3f}|}}{{{t2} - {t1}}}")
            st.success(rf" Resposta: {v_media:.4f} M/s")
        if mostrar_alvo: 
            fig_main.add_trace(go.Scatter(x=[t1, t2], y=[c1, c2], mode='markers+lines+text', name='Secante', text=[f"{c1:.3f}M", f"{c2:.3f}M"], textposition=["bottom left", "top right"], line=dict(color='yellow', dash='dash', width=2)))

    elif modo_calc == "Velocidade Instantânea":
        st.subheader(f"Cálculo da Velocidade Instantânea de {nome_alvo}")
        ti = st.slider("Escolha o instante (t)", 0.0, t_limite, float(t_limite/2), key="K16_VI_TI")
        ci = np.interp(ti, t, conc_alvo)
        vi = k_sid * (np.interp(ti, t, conc_a)**ordem_a_sid) * (np.interp(ti, t, conc_b)**ordem_b_sid if modelo == "A + B → Produto" else 1)
        slope, b_coef = -vi, ci - (-vi * ti)
        t_int_x = -b_coef / slope if slope != 0 else t_max
        delta_c, delta_t = -b_coef, t_int_x
        st.write(f"Use os pontos da reta tangente para encontrar $m$ e a equação da reta para {nome_alvo}:")
        st.latex(rf"m = \frac{{\Delta {nome_alvo}}}{{\Delta t}} \quad \rightarrow \quad v_{{inst}} = -m")
        st.info(f"**Dados da Reta Tangente no gráfico:** \n\n $\Delta {nome_alvo} = {delta_c:.3f}$ M\n\n $\Delta t = {delta_t:.3f}$ s")
        if st.button("Revelar Velocidade e Equação", key="K17_BTN_VI"):
            st.latex(rf"m = \frac{{{delta_c:.3f}}}{{{delta_t:.3f}}} = {slope:.4f}")
            st.success(rf" Velocidade ( $v = -m$ ): {vi:.4f} M/s")
            st.write(f" Equação da Reta Tangente: ")
            st.latex(rf"{nome_alvo} = {slope:.4f} \cdot t {'+' if b_coef >= 0 else '-'} {abs(b_coef):.4f}")
        if st.button(f"📥 Salvar Ponto da Tangente", key="BTN_COLETAR_PONTO"):
            if 'pontos_taxa' not in st.session_state: st.session_state.pontos_taxa = []
            st.session_state.pontos_taxa.append({'[C]': float(ci), 'Velocidade': float(vi)})
        if mostrar_alvo:
            fig_main.add_trace(go.Scatter(x=[0, t_int_x], y=[b_coef, 0], mode='lines', name='Tangente', line=dict(color='cyan', width=2)))
            fig_main.add_trace(go.Scatter(x=[ti], y=[ci], mode='markers', name='Instante (t)', marker=dict(color='White', size=10, symbol='circle', line=dict(color='black', width=2))))
            fig_main.add_trace(go.Scatter(x=[0, t_int_x], y=[b_coef, 0], mode='markers+text', name='Interceptos', text=[f"(0.00, {b_coef:.2f} M)", f"({t_int_x:.2f} s, 0.00)"], textposition="top right", marker=dict(color='yellow', size=10, symbol='x')))
            fig_main.add_trace(go.Scatter(x=[0, 0, t_int_x], y=[0, b_coef, 0], mode='lines', showlegend=False, line=dict(color='cyan', dash='dot', width=2)))

with col1: 
    fig_main.update_layout(xaxis_title="Tempo (s)", yaxis_title="Molaridade (M)", template="plotly_dark")
    st.plotly_chart(fig_main, use_container_width=True, key="CHART_1_PRINCIPAL")

# =====================================================================
# --- MÉTODO DIFERENCIAL (DAVIDSON COLLEGE) ---
# =====================================================================
st.divider()
st.header("🔬 Método Diferencial: Velocidade vs Concentração")
c_t1, c_t2 = st.columns([2, 1])

with c_t2:
    st.write("### Coleta de Dados")
    st.write("Inspirado no **Davidson College**, você precisa agir como um pesquisador!")
    st.markdown("1. Use a Velocidade Instantânea acima.\n2. Meça a tangente em vários tempos diferentes.\n3. Salve os pontos para montar sua curva.")
    linearizar_dif = st.checkbox("Plotar ln(v) vs ln[C] para achar a Ordem", key="CHK_LOG_LOG")
    mostrar_tendencia = st.checkbox("📈 Traçar Linha de Tendência", key="CHK_TENDENCIA")
    if st.button("🗑️ Limpar Pontos Coletados"):
        st.session_state.pontos_taxa = []
        st.rerun()
    if 'pontos_taxa' in st.session_state and len(st.session_state.pontos_taxa) > 0:
        st.dataframe(st.session_state.pontos_taxa, hide_index=True, use_container_width=True)

with c_t1:
    fig_taxa = go.Figure()
    if 'pontos_taxa' in st.session_state and len(st.session_state.pontos_taxa) > 0:
        c_vals = np.array([p['[C]'] for p in st.session_state.pontos_taxa])
        v_vals = np.array([p['Velocidade'] for p in st.session_state.pontos_taxa])
        log_c, log_v = np.log(c_vals + 1e-9), np.log(v_vals + 1e-9)
        if linearizar_dif:
            fig_taxa.add_trace(go.Scatter(x=log_c, y=log_v, mode='markers', name='Dados', marker=dict(color='cyan', size=10)))
            fig_taxa.update_layout(xaxis_title=f"ln({nome_alvo})", yaxis_title="ln(v)")
            if mostrar_tendencia and len(set(log_c)) > 1:
                z = np.polyfit(log_c, log_v, 1)
                xr = np.linspace(min(log_c), max(log_c), 100)
                fig_taxa.add_trace(go.Scatter(x=xr, y=np.poly1d(z)(xr), mode='lines', name=f'Ajuste (m={z[0]:.2f})', line=dict(color='yellow', dash='dash', width=2)))
        else:
            fig_taxa.add_trace(go.Scatter(x=c_vals, y=v_vals, mode='markers', name='Medições', marker=dict(color='magenta', size=12, symbol='x')))
            fig_taxa.update_layout(xaxis_title=f"Concentração {nome_alvo} (M)", yaxis_title="Velocidade Instantânea (M/s)", xaxis=dict(autorange="reversed"))
            if mostrar_tendencia and len(set(c_vals)) > 1:
                z = np.polyfit(log_c, log_v, 1)
                cs = np.linspace(min(c_vals), max(c_vals), 100)
                fig_taxa.add_trace(go.Scatter(x=cs, y=np.exp(z[1])*(cs**z[0]), mode='lines', name='Curva de Melhor Ajuste', line=dict(color='yellow', dash='dash', width=2)))
    else:
        fig_taxa.add_annotation(text="Nenhum ponto coletado. Salve pontos medindo a tangente acima!", showarrow=False, font=dict(color="yellow", size=14))
        fig_taxa.update_layout(xaxis_title=f"Concentração {nome_alvo} (M)", yaxis_title="Velocidade Instantânea (M/s)")
    fig_taxa.update_layout(template="plotly_dark", height=400)
    st.plotly_chart(fig_taxa, use_container_width=True, key="CHART_4_TAXA_DIF")

# --- 2. Linearização ---
st.divider()
st.subheader(f"📈 Linearização para {nome_alvo}")
c_l1, c_l2 = st.columns([2, 1])
if ordem_alvo == 0: y_lin, lab_lin = conc_alvo, nome_alvo
elif ordem_alvo == 1: y_lin, lab_lin = np.log(conc_alvo + 1e-9), f"ln({nome_alvo})"
else: y_lin, lab_lin = 1/(conc_alvo + 1e-9), f"1/{nome_alvo}"

with c_l2:
    st.write("### Encontre a Constante $k$")
    st.write("A inclinação ( $m$ ) desta reta corresponde ao valor de k !")
    t_r_max = float(t[-1])
    t1_lin = st.number_input("Escolha t1", 0.0, t_r_max, min(1.0, t_r_max/4), key="LIN_T1")
    t2_lin = st.number_input("Escolha t2", 0.0, t_r_max, min(5.0, t_r_max/2), key="LIN_T2")
    y1_lin, y2_lin = np.interp(t1_lin, t, y_lin), np.interp(t2_lin, t, y_lin)
    m_lin = (y2_lin - y1_lin) / (t2_lin - t1_lin) if t2_lin != t1_lin else 0
    k_calc = -m_lin if ordem_alvo <= 1 else m_lin
    st.latex(rf"m = \frac{{\Delta y}}{{\Delta x}} \quad \rightarrow \quad k = {'-m' if ordem_alvo <= 1 else 'm'}")
    if st.button("Calcular $k$ pelo Gráfico", key="K25_BTN_LIN"):
        st.latex(rf"m = \frac{{{y2_lin:.3f} - ({y1_lin:.3f})}}{{{t2_lin} - {t1_lin}}}")
        st.success(rf" Constante $k$ calculada: {abs(k_calc):.4f}")

with c_l1:
    fig_lin = go.Figure(go.Scatter(x=t, y=y_lin, name="Linearização", line=dict(color='orange', width=2)))
    fig_lin.add_trace(go.Scatter(x=[t1_lin, t2_lin], y=[y1_lin, y2_lin], mode='markers+text', text=[f"y={y1_lin:.2f}", f"y={y2_lin:.2f}"], textposition="top right", marker=dict(color='white', symbol='x', size=10)))
    fig_lin.update_layout(height=350, template="plotly_dark", yaxis_title=lab_lin, xaxis_title="Tempo (s)", xaxis=dict(range=[0, t_r_max]))
    st.plotly_chart(fig_lin, use_container_width=True, key="CHART_2_LINEAR")

# --- 3. Comparador Histórico ---
st.divider()
st.header("📚 Comparador de Curvas Cinéticas")
if 'historico' not in st.session_state: st.session_state.historico = []
h1, h2, h3 = st.columns(3)
with h1: n_comp = st.number_input("Ordem", 0.0, 3.0, 1.0, step=0.5, key="K18_HIST_N")
with h2: c_comp = st.number_input("[A]₀", 0.1, 10.0, 2.0, key="K19_HIST_C")
with h3: k_comp = st.number_input("k", 0.01, 5.0, 0.45, key="K20_HIST_K")
if st.button("🚀 Gravar Curva", key="K21_BTN_GRAVAR"):
    tc = np.linspace(0, t_max, 1000)
    sc = odeint(lambda y, t, k, n: [-k*(y[0]**n)], [c_comp], tc, args=(k_comp, n_comp))
    st.session_state.historico.append({'t': tc, 'y': sc[:, 0], 'label': f"Ordem: {n_comp} | [A]₀: {c_comp:.2f} | k: {k_comp:.2f}"})
if st.button("🗑️ Resetar Histórico", key="K22_BTN_RESET"): st.session_state.historico = []; st.rerun()
fig_h = go.Figure()
for c in st.session_state.historico: fig_h.add_trace(go.Scatter(x=c['t'], y=c['y'], name=c['label'], mode='lines'))
fig_h.update_layout(xaxis=dict(title="Tempo (s)"), yaxis=dict(title="Conc. [A]"), height=450, template="plotly_dark")
st.plotly_chart(fig_h, use_container_width=True, key="CHART_3_HISTORICO")

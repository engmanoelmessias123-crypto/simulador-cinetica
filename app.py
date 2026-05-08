import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.integrate import odeint

st.set_page_config(page_title="Laboratório de Cinética Prof", layout="wide")

# --- Ocultar o Menu e Toolbar (Versão Definitiva) ---
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
    st.sidebar.success("**Modo Ativado!**\nVá na aba de Linearização e descubra a Ordem e a constante 'k'.")
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

# Trava da Realidade Física
limite_zero = 1e-5
indices_validos = (conc_a > limite_zero) & (conc_b > limite_zero if modelo == "A + B → Produto" else True)
t, conc_a, conc_p = t[indices_validos], conc_a[indices_validos], conc_p[indices_validos]
if modelo == "A + B → Produto": conc_b = conc_b[indices_validos]

# --- Opções de Exibição ---
st.sidebar.divider()
mostrar_a = st.sidebar.checkbox("Reagente [A]", value=True)
mostrar_b = st.sidebar.checkbox("Reagente [B]", value=True) if modelo == "A + B → Produto" else False
mostrar_p = st.sidebar.checkbox("Produto", value=True)
mostrar_meia_vida = st.sidebar.checkbox("⏱️ Meia-Vida (t½)", value=False) if (not modo_desafio and modelo == "A → Produto") else False

st.sidebar.divider()
modo_calc = st.sidebar.selectbox("O que calcular?", ["Nenhum", "Velocidade Média", "Velocidade Instantânea"])
reagente_alvo = st.sidebar.radio("Analisar qual?", ["A", "B"]) if modo_calc != "Nenhum" and modelo == "A + B → Produto" else "A"
conc_alvo, nome_alvo = (conc_a, f"[{reagente_alvo}]"), (conc_a if reagente_alvo == "A" else conc_b), f"[{reagente_alvo}]"
mostrar_alvo = mostrar_a if reagente_alvo == "A" else mostrar_b

# --- 1. Gráfico Principal ---
st.title("🧪 Simulação da Velocidade da Reação")
col1, col2 = st.columns([2, 1])
fig_main = go.Figure()
if mostrar_a: fig_main.add_trace(go.Scatter(x=t, y=conc_a, name="[A]", line=dict(color='red', width=3)))
if mostrar_b: fig_main.add_trace(go.Scatter(x=t, y=conc_b, name="[B]", line=dict(color='green', width=3)))
if mostrar_p: fig_main.add_trace(go.Scatter(x=t, y=conc_p, name="[Produto]", line=dict(color='blue', width=3)))

if mostrar_meia_vida:
    c_at, t_at = a0_sid, 0.0
    for i in range(1, 5):
        t_m = c_at/(2*k_sid) if ordem_a_sid==0 else (np.log(2)/k_sid if ordem_a_sid==1 else 1/(k_sid*c_at))
        t_at += t_m
        c_at /= 2
        if t_at > t[-1]: break
        fig_main.add_shape(type="line", x0=t_at, x1=t_at, y0=0, y1=c_at, line=dict(color="orange", width=1, dash="dot"))
        fig_main.add_shape(type="line", x0=0, x1=t_at, y0=c_at, y1=c_at, line=dict(color="orange", width=1, dash="dot"))
        fig_main.add_trace(go.Scatter(x=[t_at], y=[c_at], mode='markers+text', text=[f"{t_at:.1f}s"], textposition="top right", marker=dict(color='orange', size=8, symbol='diamond'), name=f'{i}º t½'))

with col2:
    t_lim = float(t[-1])
    if modo_calc == "Velocidade Média":
        st.subheader(f"Cálculo da Velocidade Média de {nome_alvo}")
        t1 = st.number_input("Escolha t1", 0.0, t_lim, min(1.0, t_lim/4), key="VM1")
        t2 = st.number_input("Escolha t2", 0.0, t_lim, min(5.0, t_lim/2), key="VM2")
        c1, c2 = np.interp(t1, t, conc_alvo[1]), np.interp(t2, t, conc_alvo[1])
        v_m = abs(c2 - c1) / (t2 - t1) if t2 != t1 else 0
        st.latex(rf"v_m = \left| \frac{{\Delta {nome_alvo}}}{{\Delta t}} \right|")
        if st.button("Revelar Velocidade Média"):
            st.latex(rf"v_m = \frac{{|{c2:.3f} - {c1:.3f}|}}{{{t2} - {t1}}}")
            st.success(f"Resposta: {v_m:.4f} M/s")
        if mostrar_alvo:
            fig_main.add_trace(go.Scatter(x=[t1, t2], y=[c1, c2], mode='markers+lines+text', name='Secante', text=[f"{c1:.2f}M", f"{c2:.2f}M"], line=dict(color='yellow', dash='dash')))

    elif modo_calc == "Velocidade Instantânea":
        st.subheader(f"Cálculo da Velocidade Instantânea de {nome_alvo}")
        ti = st.slider("Escolha o instante (t)", 0.0, t_lim, t_lim/2)
        ci = np.interp(ti, t, conc_alvo[1])
        vi = k_sid * (np.interp(ti, t, conc_a)**ordem_a_sid) * (np.interp(ti, t, conc_b)**(ordem_b_sid if modelo=="A+B → Produto" else 0) if modelo=="A+B → Produto" else 1)
        slope, b_c = -vi, ci - (-vi * ti)
        t_int_x = -b_c/slope if slope != 0 else t_max
        st.write(f"Use os pontos da reta tangente para encontrar $m$ e a equação:")
        st.latex(rf"m = \frac{{\Delta {nome_alvo}}}{{\Delta t}} \quad \rightarrow \quad v_{{inst}} = -m")
        st.info(f"**Dados da Reta Tangente:**\n\n$\Delta {nome_alvo} = {-b_c:.3f}$ M\n\n$\Delta t = {t_int_x:.3f}$ s")
        if st.button("Revelar Velocidade e Equação"):
            st.latex(rf"m = \frac{{{-b_c:.3f}}}{{{t_int_x:.3f}}} = {slope:.4f}")
            st.success(f"Velocidade: {vi:.4f} M/s")
            st.latex(rf"{nome_alvo} = {slope:.4f} \cdot t + {b_c:.4f}")
        if st.button("📥 Salvar Ponto da Tangente"):
            if 'pontos_taxa' not in st.session_state: st.session_state.pontos_taxa = []
            st.session_state.pontos_taxa.append({'[C]': float(ci), 'Velocidade': float(vi)})
        
        if mostrar_alvo:
            fig_main.add_trace(go.Scatter(x=[0, t_int_x], y=[b_c, 0], mode='lines', name='Tangente', line=dict(color='cyan', width=2)))
            fig_main.add_trace(go.Scatter(x=[ti], y=[ci], mode='markers', name='Ponto Medido', marker=dict(color='white', size=10, symbol='circle', line=dict(color='black', width=2))))
            fig_main.add_trace(go.Scatter(x=[0, t_int_x], y=[b_c, 0], mode='markers+text', text=[f"(0.00, {b_c:.2f} M)", f"({t_int_x:.2f} s, 0.00)"], textposition="top right", marker=dict(color='yellow', symbol='x'), name="Interceptos"))
            fig_main.add_trace(go.Scatter(x=[0, 0, t_int_x], y=[0, b_c, 0], mode='lines', showlegend=False, line=dict(color='cyan', dash='dot', width=2)))

with col1:
    fig_main.update_layout(xaxis_title="Tempo (s)", yaxis_title="Molaridade (M)", template="plotly_dark")
    st.plotly_chart(fig_main, use_container_width=True)

# --- Método Diferencial ---
st.divider()
st.header("🔬 Método Diferencial: Velocidade vs Concentração")
c_t1, c_t2 = st.columns([2, 1])
with c_t2:
    st.write("### Coleta de Dados")
    st.write("Inspirado no **Davidson College**, aja como um pesquisador!")
    st.markdown("1. Use a Velocidade Instantânea acima.\n2. Meça a tangente em tempos diferentes.\n3. Salve os pontos para montar sua curva.")
    linearizar_dif = st.checkbox("Plotar ln(v) vs ln[C] para achar a Ordem", key="LOGLOG")
    mostrar_tendencia = st.checkbox("📈 Traçar Linha de Tendência", key="TRD")
    if st.button("🗑️ Limpar Pontos"): st.session_state.pontos_taxa = []; st.rerun()
    if 'pontos_taxa' in st.session_state and st.session_state.pontos_taxa: st.dataframe(st.session_state.pontos_taxa, hide_index=True)

with c_t1:
    fig_taxa = go.Figure()
    if 'pontos_taxa' in st.session_state and st.session_state.pontos_taxa:
        c_vals = np.array([p['[C]'] for p in st.session_state.pontos_taxa])
        v_vals = np.array([p['Velocidade'] for p in st.session_state.pontos_taxa])
        log_c, log_v = np.log(c_vals + 1e-9), np.log(v_vals + 1e-9)
        if linearizar_dif:
            fig_taxa.add_trace(go.Scatter(x=log_c, y=log_v, mode='markers', name='Dados', marker=dict(color='cyan', size=10)))
            fig_taxa.update_layout(xaxis_title=f"ln({nome_alvo})", yaxis_title="ln(v)")
            if mostrar_tendencia and len(set(log_c)) > 1:
                z = np.polyfit(log_c, log_v, 1)
                xr = np.linspace(log_c.min(), log_c.max(), 100)
                fig_taxa.add_trace(go.Scatter(x=xr, y=np.poly1d(z)(xr), mode='lines', name=f'Tendência (Ordem m={z[0]:.2f})', line=dict(color='yellow', dash='dash', width=2)))
        else:
            fig_taxa.add_trace(go.Scatter(x=c_vals, y=v_vals, mode='markers', name='Medições', marker=dict(color='magenta', symbol='x', size=12)))
            if mostrar_tendencia:
                if len(set(v_vals)) == 1 or (ordem_a_sid == 0 and not modo_desafio):
                    fig_taxa.add_trace(go.Scatter(x=[c_vals.min(), c_vals.max()], y=[v_vals[0], v_vals[0]], mode='lines', name='Ajuste (v=k)', line=dict(color='yellow', dash='dash', width=2)))
                elif len(set(c_vals)) > 1:
                    z = np.polyfit(log_c, log_v, 1)
                    cs = np.linspace(c_vals.min(), c_vals.max(), 100)
                    fig_taxa.add_trace(go.Scatter(x=cs, y=np.exp(z[1])*(cs**z[0]), mode='lines', name='Curva de Ajuste', line=dict(color='yellow', dash='dash', width=2)))
            fig_taxa.update_layout(xaxis_title=f"Concentração {nome_alvo} (M)", yaxis_title="Velocidade (M/s)", xaxis=dict(autorange="reversed"))
    else: fig_taxa.add_annotation(text="Salve pontos da tangente acima!", showarrow=False, font=dict(color="yellow", size=14))
    fig_taxa.update_layout(template="plotly_dark", height=400)
    st.plotly_chart(fig_taxa, use_container_width=True)

# --- 2. Linearização Inteligente ---
st.divider()
st.subheader(f"📈 Linearização para {nome_alvo}")
c_l1, c_l2 = st.columns([2, 1])
y_lin, lab_lin = (conc_alvo[1], nome_alvo) if ordem_a_sid==0 else ((np.log(conc_alvo[1]+1e-9), f"ln({nome_alvo})") if ordem_a_sid==1 else (1/(conc_alvo[1]+1e-9), f"1/{nome_alvo}"))
with c_l2:
    st.write("### Calcule a Constante $k$")
    st.write("A inclinação ($m$) desta reta corresponde ao valor de k!")
    t_r_max = float(t[-1])
    t1_l = st.number_input("Escolha t1", 0.0, t_r_max, float(t_r_max/4), key="L1")
    t2_l = st.number_input("Escolha t2", 0.0, t_r_max, float(t_r_max/2), key="L2")
    y1_l, y2_l = np.interp(t1_l,

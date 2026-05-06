import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.integrate import odeint

st.set_page_config(page_title="Laboratório de Cinética Prof", layout="wide")

# --- Lógica de Cálculo (Equações Diferenciais) ---
def modelo_cinetico(y, t, k, na, nb, tipo):
    A = y[0]
    B = y[1] if tipo == "A + B → Produto" else 0
    velocidade = k * (A**na) * (B**nb if nb > 0 else 1)
    dAdt = -velocidade
    dPdt = velocidade
    return [dAdt, -velocidade, dPdt] if tipo == "A + B → Produto" else [dAdt, dPdt]

# --- Sidebar: Configurações da Reação ---
st.sidebar.title("Configurações")
modelo = st.sidebar.radio("Tipo de Reação", ["A → Produto", "A + B → Produto"])
k = st.sidebar.slider("Constante k", 0.01, 2.0, 0.45)
ordem_a = st.sidebar.slider("Ordem em A", 0, 2, 1)
a0 = st.sidebar.slider("[A]₀ Inicial", 0.1, 5.0, 2.0)
t_max = st.sidebar.slider("Tempo Total", 10, 100, 50)

# --- Resolução da Cinética ---
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

# --- Sidebar: Opções de Exibição ---
st.sidebar.divider()
st.sidebar.subheader("👁️ Exibir no gráfico?")
mostrar_a = st.sidebar.checkbox("Reagente [A] (Vermelho)", value=True)
mostrar_b = st.sidebar.checkbox("Reagente [B] (Verde)", value=True) if modelo == "A + B → Produto" else False
mostrar_p = st.sidebar.checkbox("Produto (Azul)", value=True)

# --- Sidebar: Ferramentas Pedagógicas ---
st.sidebar.divider()
st.sidebar.subheader("🧮 Ferramentas de Cálculo")
modo_calc = st.sidebar.selectbox("O que calcular?", ["Nenhum", "Velocidade Média", "Velocidade Instantânea"])

reagente_alvo = "A"
if modo_calc != "Nenhum" and modelo == "A + B → Produto":
    reagente_alvo = st.sidebar.radio("Qual reagente analisar?", ["A", "B"])

conc_alvo = conc_a if reagente_alvo == "A" else conc_b
nome_alvo = f"[{reagente_alvo}]"
ordem_alvo = ordem_a if reagente_alvo == "A" else ordem_b
mostrar_alvo = mostrar_a if reagente_alvo == "A" else mostrar_b

# --- Interface Principal ---
st.title("🧪 Verificador de Velocidade Cinética")
col1, col2 = st.columns([2, 1])

fig = go.Figure()
if mostrar_a:
    fig.add_trace(go.Scatter(x=t, y=conc_a, name="[A]", line=dict(color='red', width=3)))
if mostrar_b and modelo == "A + B → Produto":
    fig.add_trace(go.Scatter(x=t, y=conc_b, name="[B]", line=dict(color='green', width=3)))
if mostrar_p:
    fig.add_trace(go.Scatter(x=t, y=conc_p, name="[Produto]", line=dict(color='blue', width=3)))

# --- Lógica das Ferramentas ("O Jogo") ---
if modo_calc == "Velocidade Média":
    with col2:
        st.subheader(f"Velocidade Média de {nome_alvo}")
        t1 = st.number_input("t1", 0.0, float(t_max), 5.0)
        t2 = st.number_input("t2", 0.0, float(t_max), 15.0)
        c1 = np.interp(t1, t, conc_alvo)
        c2 = np.interp(t2, t, conc_alvo)
        v_media = abs(c2 - c1) / (t2 - t1) if t2 != t1 else 0
        st.latex(rf"v_m = \left| \frac{{\Delta {nome_alvo}}}{{\Delta t}} \right|")
        if st.button("Revelar VM"):
            st.success(rf"v_m = {v_media:.4f} M/s")
    if mostrar_alvo:
        fig.add_trace(go.Scatter(x=[t1, t2], y=[c1, c2], mode='markers+lines+text', name='Secante',
                                 text=[f"{c1:.3f}M", f"{c2:.3f}M"], textfont=dict(color="yellow"),
                                 line=dict(color='yellow', dash='dash')))

elif modo_calc == "Velocidade Instantânea":
    with col2:
        st.subheader(f"Velocidade Instantânea de {nome_alvo}")
        ti = st.slider("Instante (t)", 0.0, float(t_max), float(t_max/2))
        ci = np.interp(ti, t, conc_alvo)
        ai_v, bi_v = np.interp(ti, t, conc_a), np.interp(ti, t, conc_b)
        vi = k * (ai_v**ordem_a) * (bi_v**ordem_b if modelo == "A + B → Produto" and ordem_b > 0 else 1)
        slope = -vi
        b_coef = ci - slope * ti
        dt = t_max * 0.15
        t_s, t_e = max(0, ti-dt), min(t_max, ti+dt)
        c_s, c_e = ci + slope*(t_s-ti), ci + slope*(t_e-ti)
        st.info(f"Δ{nome_alvo} = {c_e-c_s:.3f} M | Δt = {t_e-t_s:.3f} s")
        if st.button("Revelar VI e Equação"):
            st.success(rf"v = {vi:.4f} M/s")
            st.latex(rf"{nome_alvo} = {slope:.4f}t {'+' if b_coef>=0 else '-'} {abs(b_coef):.4f}")
    if mostrar_alvo:
        fig.add_trace(go.Scatter(x=[t_s, t_e], y=[c_s, c_e], mode='lines', name='Tangente', line=dict(color='cyan')))
        fig.add_trace(go.Scatter(x=[t_s, t_s, t_e], y=[c_s, c_e, c_e], mode='lines', showlegend=False, line=dict(color='cyan', dash='dot')))

with col1:
    fig.update_layout(xaxis_title="Tempo (s)", yaxis_title="Molaridade (M)", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

# --- NOVO: Gráfico de Linearização (Abaixo) ---
st.divider()
st.subheader(f"📈 Análise de Linearização para {nome_alvo}")
c_l1, c_l2 = st.columns([2, 1])

with c_l1:
    if ordem_alvo == 0: y_lin, lab_lin = conc_alvo, f"{nome_alvo}"
    elif ordem_alvo == 1: y_lin, lab_lin = np.log(conc_alvo + 1e-9), f"ln({nome_alvo})"
    else: y_lin, lab_lin = 1 / (conc_alvo + 1e-9), f"1 / {nome_alvo}"
    
    fig_lin = go.Figure(go.Scatter(x=t, y=y_lin, line=dict(color='orange', width=2)))
    fig_lin.update_layout(height=350, xaxis_title="Tempo (s)", yaxis_title=lab_lin, template="plotly_dark")
    st.plotly_chart(fig_lin, use_container_width=True)
with c_l2:
    st.write(f"**Ordem Experimental Detectada: {ordem_alvo}**")
    st.write(f"Para ordem {ordem_alvo}, o gráfico de `{lab_lin}` vs tempo deve ser linear.")
    st.info("💡 Peça para os alunos mudarem a ordem no slider e observarem qual gráfico 'estica' até virar uma reta!")



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

# --- Sidebar: Configurações da Reação ---
st.sidebar.title("Configurações")
modelo = st.sidebar.radio("Tipo de Reação", ["A → Produto", "A + B → Produto"], key="radio_modelo")
k_sid = st.sidebar.slider("Constante k", 0.01, 2.0, 0.45, key="k_slider")
ordem_a_sid = st.sidebar.slider("Ordem em A", 0, 2, 1, key="ordem_a_slider")
a0_sid = st.sidebar.slider("[A]₀ Inicial", 0.1, 5.0, 2.0, key="a0_slider")
t_max = st.sidebar.slider("Tempo Total", 10, 100, 50, key="t_max_slider")

# Resolução Cinética Principal
t = np.linspace(0, t_max, 1000)
if modelo == "A + B → Produto":
    b0_sid = st.sidebar.slider("[B]₀ Inicial", 0.1, 5.0, 2.0, key="b0_slider")
    ordem_b_sid = st.sidebar.slider("Ordem em B", 0, 2, 2, key="ordem_b_slider")
    sol = odeint(modelo_cinetico, [a0_sid, b0_sid, 0], t, args=(k_sid, ordem_a_sid, ordem_b_sid, modelo))
    conc_a, conc_b, conc_p = sol[:, 0], sol[:, 1], sol[:, 2]
else:
    sol = odeint(modelo_cinetico, [a0_sid, 0], t, args=(k_sid, ordem_a_sid, 0, modelo))
    conc_a, conc_p = sol[:, 0], sol[:, 1]
    conc_b = np.zeros_like(t)

# --- Opções de Exibição ---
st.sidebar.divider()
st.sidebar.subheader("👁️ Exibir no gráfico?")
mostrar_a = st.sidebar.checkbox("Reagente [A]", value=True, key="check_a")
mostrar_b = st.sidebar.checkbox("Reagente [B]", value=True, key="check_b") if modelo == "A + B → Produto" else False
mostrar_p = st.sidebar.checkbox("Produto", value=True, key="check_p")

# --- Ferramentas de Cálculo ---
st.sidebar.divider()
st.sidebar.subheader("🧮 Ferramentas")
modo_calc = st.sidebar.selectbox("O que calcular?", ["Nenhum", "Velocidade Média", "Velocidade Instantânea"], key="select_calc")

reagente_alvo = "A"
if modo_calc != "Nenhum" and modelo == "A + B → Produto":
    reagente_alvo = st.sidebar.radio("Analisar qual?", ["A", "B"], key="radio_alvo")

conc_alvo = conc_a if reagente_alvo == "A" else conc_b
nome_alvo = f"[{reagente_alvo}]"
ordem_alvo = ordem_a_sid if reagente_alvo == "A" else (ordem_b_sid if modelo == "A + B → Produto" else 0)
mostrar_alvo = mostrar_a if reagente_alvo == "A" else mostrar_b

# --- Interface Principal ---
st.title("🧪 Verificador de Velocidade Cinética")
col1, col2 = st.columns([2, 1])

fig = go.Figure()
if mostrar_a: fig.add_trace(go.Scatter(x=t, y=conc_a, name="[A]", line=dict(color='red', width=3)))
if mostrar_b and modelo == "A + B → Produto": fig.add_trace(go.Scatter(x=t, y=conc_b, name="[B]", line=dict(color='green', width=3)))
if mostrar_p: fig.add_trace(go.Scatter(x=t, y=conc_p, name="[Produto]", line=dict(color='blue', width=3)))

# Lógica VM/VI
if modo_calc == "Velocidade Média":
    with col2:
        st.subheader(f"VM de {nome_alvo}")
        t1 = st.number_input("t1", 0.0, float(t_max), 5.0, key="vm_t1")
        t2 = st.number_input("t2", 0.0, float(t_max), 15.0, key="vm_t2")
        c1, c2 = np.interp(t1, t, conc_alvo), np.interp(t2, t, conc_alvo)
        if st.button("Revelar VM", key="btn_vm"):
            st.success(f"vm = {abs(c2-c1)/(t2-t1):.4f} M/s")
    if mostrar_alvo: fig.add_trace(go.Scatter(x=[t1, t2], y=[c1, c2], mode='markers+lines', name='Secante', line=dict(color='yellow', dash='dash')))

elif modo_calc == "Velocidade Instantânea":
    with col2:
        st.subheader(f"VI de {nome_alvo}")
        ti = st.slider("Instante (t)", 0.0, float(t_max), float(t_max/2), key="vi_ti")
        ci = np.interp(ti, t, conc_alvo)
        vi = k_sid * (np.interp(ti, t, conc_a)**ordem_a_sid) * (np.interp(ti, t, conc_b)**(ordem_b_sid if modelo == "A + B → Produto" else 0) if modelo == "A + B → Produto" else 1)
        st.info(f"Inclinação no ponto: {ci:.3f} M")
        if st.button("Revelar VI", key="btn_vi"):
            st.success(f"v = {vi:.4f} M/s")

with col1:
    fig.update_layout(xaxis_title="Tempo (s)", yaxis_title="Molaridade (M)", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

# --- Linearização ---
st.divider()
st.subheader(f"📈 Linearização para {nome_alvo}")
c_l1, c_l2 = st.columns([2, 1])
with c_l1:
    if ordem_alvo == 0: y_lin, lab_lin = conc_alvo, nome_alvo
    elif ordem_alvo == 1: y_lin, lab_lin = np.log(conc_alvo + 1e-9), f"ln({nome_alvo})"
    else: y_lin, lab_lin = 1/(conc_alvo + 1e-9), f"1/{nome_alvo}"
    fig_lin = go.Figure(go.Scatter(x=t, y=y_lin, line=dict(color='orange', width=2)))
    fig_lin.update_layout(height=300, template="plotly_dark", yaxis_title=lab_lin)
    st.plotly_chart(fig_lin, use_container_width=True)

# --- COMPARADOR (Ajustado para o seu gosto) ---
st.divider()
st.header("📚 Comparador de Histórico (Foco na Inclinação)")
if 'historico' not in st.session_state: st.session_state.historico = []

h1, h2, h3 = st.columns(3)
with h1: n_comp = st.number_input("Ordem", 0.0, 3.0, 1.0, step=0.5, key="comp_n")
with h2: c_comp = st.number_input("[A]₀", 0.1, 10.0, 2.0, key="comp_c")
with h3: k_comp = st.number_input("k", 0.01, 5.0, 0.45, key="comp_k")

b_g, b_r = st.columns(2)
with b_g:
    if st.button("🚀 Gravar Curva", key="btn_gravar"):
        t_c = np.linspace(0, t_max, 1000)
        sol_c = odeint(lambda y, t, k, n: [-k*(y[0]**n)], [c_comp], t_c, args=(k_comp, n_comp))
        st.session_state.historico.append({'t': t_c, 'y': sol_c[:, 0], 'label': f"Ordem {n_comp} | [A]₀ {c_comp}"})
with b_r:
    if st.button("🗑️ Resetar Histórico", key="btn_reset"):
        st.session_state.historico = []
        st.rerun()

fig_h = go.Figure()
if not st.session_state.historico:
    fig_h.add_annotation(text="Adicione curvas para comparar", showarrow=False)
else:
    for c in st.session_state.historico:
        fig_h.add_trace(go.Scatter(x=c['t'], y=c['y'], name=c['label'], mode='lines'))

# O ZOOM QUE VOCÊ QUERIA (Foco nos primeiros 10 segundos)
fig_h.update_layout(
    xaxis=dict(title="Tempo (s)", range=[0, 10]), 
    yaxis=dict(title="Conc. [A]", range=[0, 5]),
    height=450, template="plotly_dark"
)
st.plotly_chart(fig_h, use_container_width=True)

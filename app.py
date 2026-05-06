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

# --- NOVA SEÇÃO: Simulador de Comparação de Ordens ---
st.divider()
st.header("🔬 Simulador de Impacto da Ordem")
st.write("Aqui você pode ver como a curvatura muda apenas alterando a ordem, mantendo o mesmo $k$ e $[A]_0$.")

ordem_comparativa = st.select_slider(
    "Aumente a Ordem da Reação:",
    options=[0, 1, 2, 3]
)

# --- SEÇÃO: Comparador de Histórico (Curvas Gravadas) ---
st.divider()
st.header("📚 Histórico de Comparação Cinética")
st.write("Adicione curvas ao gráfico para comparar ordens e concentrações diferentes.")

# Inicializa a memória se ela não existir
if 'historico_curvas' not in st.session_state:
    st.session_state.historico_curvas = []

# Controles locais da seção
c1, c2, c3 = st.columns(3)
with c1:
    nova_ordem = st.number_input("Ordem p/ gravar", 0.0, 3.0, 1.0, step=0.5)
with c2:
    nova_conc = st.number_input("[A]₀ p/ gravar", 0.1, 10.0, 2.0)
with c3:
    novo_k = st.number_input("k p/ gravar", 0.01, 5.0, 0.45)

b1, b2 = st.columns(2)
with b1:
    if st.button("🚀 Gravar Curva", use_container_width=True):
        # Cálculo da nova curva
        def func_comp(y, t, k, n):
            return [-k * (y[0]**n)]
        
        t_comp = np.linspace(0, t_max, 500)
        sol_comp = odeint(func_comp, [nova_conc], t_comp, args=(novo_k, nova_ordem))
        
        # Salva no histórico com uma legenda identificadora
        legenda = f"Ordem {nova_ordem} | [A]₀ {nova_conc} | k {novo_k}"
        st.session_state.historico_curvas.append({
            't': t_comp,
            'y': sol_comp[:, 0],
            'label': legenda
        })

with b2:
    if st.button("🗑️ Resetar Gráfico", use_container_width=True):
        st.session_state.historico_curvas = []
        st.rerun()

# Plotagem do gráfico comparativo
fig_hist = go.Figure()

if not st.session_state.historico_curvas:
    fig_hist.add_annotation(text="Nenhuma curva gravada. Clique em 'Gravar Curva' acima.", 
                           showarrow=False, font=dict(size=20))
else:
    for curva in st.session_state.historico_curvas:
        fig_hist.add_trace(go.Scatter(x=curva['t'], y=curva['y'], name=curva['label'], mode='lines'))

fig_hist.update_layout(
    title="Comparativo de Cenários Cinéticos",
    xaxis_title="Tempo (s)",
    yaxis_title="Concentração [A]",
    template="plotly_dark",
    legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99)
)

st.plotly_chart(fig_hist, use_container_width=True)

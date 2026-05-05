
import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.integrate import odeint

st.set_page_config(page_title="Laboratório de Cinética", layout="wide")

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
k = st.sidebar.slider("Constante k", 0.01, 2.0, 0.2)
ordem_a = st.sidebar.slider("Ordem em A", 0, 2, 1)
a0 = st.sidebar.slider("[A]₀ Inicial", 0.1, 5.0, 2.0)
t_max = st.sidebar.slider("Tempo Total", 10, 100, 50)

# --- Resolução da Cinética ---
t = np.linspace(0, t_max, 1000)
if modelo == "A + B → Produto":
    b0 = st.sidebar.slider("[B]₀ Inicial", 0.1, 5.0, 2.0)
    ordem_b = st.sidebar.slider("Ordem em B", 0, 2, 1)
    sol = odeint(modelo_cinetico, [a0, b0, 0], t, args=(k, ordem_a, ordem_b, modelo))
    conc_a = sol[:, 0]
    conc_b = sol[:, 1]
    conc_p = sol[:, 2]
else:
    sol = odeint(modelo_cinetico, [a0, 0], t, args=(k, ordem_a, 0, modelo))
    conc_a = sol[:, 0]
    conc_p = sol[:, 1]

# --- Sidebar: Opções de Exibição do Gráfico ---
st.sidebar.divider()
st.sidebar.subheader("👁️ O que exibir no gráfico?")
mostrar_a = st.sidebar.checkbox("Reagente [A] (Vermelho)", value=True)
mostrar_b = st.sidebar.checkbox("Reagente [B] (Verde)", value=True) if modelo == "A + B → Produto" else False
mostrar_p = st.sidebar.checkbox("Produto (Azul)", value=True)

# --- Sidebar: Ferramentas Pedagógicas ---
st.sidebar.divider()
st.sidebar.subheader("🧮 Ferramentas de Cálculo")
modo_calc = st.sidebar.selectbox("O que calcular?", ["Nenhum", "Velocidade Média de [A]", "Velocidade Instantânea de [A]"])

# --- Interface Principal ---
st.title("🧪 Verificador de Velocidade Cinética")

col1, col2 = st.columns([2, 1])

# Construção do Gráfico
fig = go.Figure()

if mostrar_a:
    fig.add_trace(go.Scatter(x=t, y=conc_a, name="[A]", line=dict(color='red', width=3)))
if mostrar_b:
    fig.add_trace(go.Scatter(x=t, y=conc_b, name="[B]", line=dict(color='green', width=3)))
if mostrar_p:
    fig.add_trace(go.Scatter(x=t, y=conc_p, name="[Produto]", line=dict(color='blue', width=3)))

# Aplicação das Ferramentas ("O Jogo")
if modo_calc == "Velocidade Média de [A]":
    with col2:
        st.subheader("Cálculo da Velocidade Média")
        t1 = st.number_input("Tempo Inicial (t1)", 0.0, float(t_max), 5.0)
        t2 = st.number_input("Tempo Final (t2)", 0.0, float(t_max), 15.0)
        
        a1 = np.interp(t1, t, conc_a)
        a2 = np.interp(t2, t, conc_a)
        v_media = abs(a2 - a1) / (t2 - t1) if t2 != t1 else 0
        
        st.write("Os valores de concentração para os tempos escolhidos estão indicados no gráfico.")
        st.write("**Fórmula para os alunos:**")
        st.latex(r"v_m = \left| \frac{[A]_2 - [A]_1}{t_2 - t_1} \right|")
        
        # Botão para revelar
        if st.button("Revelar Velocidade Média"):
            st.latex(rf"v_m = \frac{{|{a2:.3f} - {a1:.3f}|}}{{{t2} - {t1}}}")
            st.success(rf"**Resposta:** {v_media:.4f} M/s")

    # Desenhar linha secante COM TEXTOS no gráfico
    if mostrar_a:
        fig.add_trace(go.Scatter(
            x=[t1, t2], y=[a1, a2], 
            mode='markers+lines+text', 
            name='Secante (V. Média)', 
            text=[f"[A]={a1:.3f}M", f"[A]={a2:.3f}M"],
            textposition=["bottom left", "top right"],
            textfont=dict(color="yellow", size=14),
            line=dict(color='yellow', dash='dash', width=2),
            marker=dict(size=10)
        ))

elif modo_calc == "Velocidade Instantânea de [A]":
    with col2:
        st.subheader("Cálculo da Velocidade Instantânea")
        ti = st.slider("Escolha o instante (t)", 0.0, float(t_max), float(t_max/2))
        
        ai = np.interp(ti, t, conc_a)
        bi = np.interp(ti, t, conc_b) if modelo == "A + B → Produto" else 0
        
        # v = k * [A]^na * [B]^nb
        vi = k * (ai**ordem_a) * (bi**ordem_b if modelo == "A + B → Produto" and ordem_b > 0 else 1)
        slope = -vi # A inclinação é negativa pois consome reagente
        
        # Cálculo da Equação da Reta (y = mx + b -> b = y - mx)
        b_coef = ai - slope * ti
        sinal_b = "+" if b_coef >= 0 else "-"
        
        # Pontos extremos da reta tangente para formar o triângulo do Delta
        dt_span = t_max * 0.15
        t_start = max(0, ti - dt_span)
        t_end = min(t_max, ti + dt_span)
        a_start = ai + slope * (t_start - ti)
        a_end = ai + slope * (t_end - ti)
        
        delta_a = a_end - a_start
        delta_t = t_end - t_start

        st.write("Use os pontos da **reta tangente** para encontrar o coeficiente angular ($m$) e a equação da reta:")
        st.latex(r"m = \frac{\Delta [A]}{\Delta t} \quad \rightarrow \quad v_{inst} = -m")
        
        # Exibindo os Deltas
        st.info(f"**Dados da Reta Tangente no gráfico:**\n\n"
                f"$\\Delta [A] = {delta_a:.3f}$ M\n\n"
                f"$\\Delta t = {delta_t:.3f}$ s")
        
        if st.button("Revelar Velocidade e Equação"):
            st.latex(rf"m = \frac{{{delta_a:.3f}}}{{{delta_t:.3f}}} = {slope:.4f}")
            st.success(rf"**Velocidade ($v = -m$):** {vi:.4f} M/s")
            
            st.write("**Equação da Reta Tangente:**")
            st.latex(rf"[A] = {slope:.4f} \cdot t {sinal_b} {abs(b_coef):.4f}")

    # Desenhar reta tangente e o triângulo de Deltas
    if mostrar_a:
        fig.add_trace(go.Scatter(
            x=[t_start, t_end], y=[a_start, a_end], 
            mode='lines', name='Tangente', 
            line=dict(color='cyan', width=2)
        ))
        fig.add_trace(go.Scatter(
            x=[ti], y=[ai], mode='markers', 
            name='Instante (t)', marker=dict(color='white', size=8)
        ))
        fig.add_trace(go.Scatter(
            x=[t_start, t_start, t_end], y=[a_start, a_end, a_end],
            mode='lines', showlegend=False,
            line=dict(color='cyan', dash='dot', width=1)
        ))

with col1:
    fig.update_layout(xaxis_title="Tempo (s)", yaxis_title="Concentração (M)", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)
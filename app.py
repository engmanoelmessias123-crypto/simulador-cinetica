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
    conc_b = np.zeros_like(t) # Apenas por segurança para não dar erro

# --- Sidebar: Opções de Exibição do Gráfico ---
st.sidebar.divider()
st.sidebar.subheader("👁️ O que exibir no gráfico?")
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

# Configurando variáveis dinâmicas com base no reagente escolhido
if reagente_alvo == "A":
    conc_alvo = conc_a
    nome_alvo = "[A]"
    mostrar_alvo = mostrar_a
else:
    conc_alvo = conc_b
    nome_alvo = "[B]"
    mostrar_alvo = mostrar_b

# --- Interface Principal ---
st.title("🧪 Verificador de Velocidade Cinética")

col1, col2 = st.columns([2, 1])

# Construção do Gráfico
fig = go.Figure()

if mostrar_a:
    fig.add_trace(go.Scatter(x=t, y=conc_a, name="[A]", line=dict(color='red', width=3)))
if mostrar_b and modelo == "A + B → Produto":
    fig.add_trace(go.Scatter(x=t, y=conc_b, name="[B]", line=dict(color='green', width=3)))
if mostrar_p:
    fig.add_trace(go.Scatter(x=t, y=conc_p, name="[Produto]", line=dict(color='blue', width=3)))

# Aplicação das Ferramentas ("O Jogo")
if modo_calc == "Velocidade Média":
    with col2:
        st.subheader(f"Cálculo da Velocidade Média de {nome_alvo}")
        t1 = st.number_input("Tempo Inicial (t1)", 0.0, float(t_max), 5.0)
        t2 = st.number_input("Tempo Final (t2)", 0.0, float(t_max), 15.0)
        
        c1 = np.interp(t1, t, conc_alvo)
        c2 = np.interp(t2, t, conc_alvo)
        v_media = abs(c2 - c1) / (t2 - t1) if t2 != t1 else 0
        
        st.write("Os valores de concentração para os tempos escolhidos estão indicados no gráfico.")
        st.write("**Fórmula para os alunos:**")
        st.latex(rf"v_m = \left| \frac{{{nome_alvo}_2 - {nome_alvo}_1}}{{t_2 - t_1}} \right|")
        
        # Botão para revelar
        if st.button("Revelar Velocidade Média"):
            st.latex(rf"v_m = \frac{{|{c2:.3f} - {c1:.3f}|}}{{{t2} - {t1}}}")
            st.success(rf"**Resposta:** {v_media:.4f} M/s")

    # Desenhar linha secante COM TEXTOS no gráfico (Só desenha se o alvo estiver visível)
    if mostrar_alvo:
        fig.add_trace(go.Scatter(
            x=[t1, t2], y=[c1, c2], 
            mode='markers+lines+text', 
            name='Secante (V. Média)', 
            text=[f"{nome_alvo}={c1:.3f}M", f"{nome_alvo}={c2:.3f}M"],
            textposition=["bottom left", "top right"],
            textfont=dict(color="yellow", size=14),
            line=dict(color='yellow', dash='dash', width=2),
            marker=dict(size=10)
        ))

elif modo_calc == "Velocidade Instantânea":
    with col2:
        st.subheader(f"Cálculo da Velocidade Instantânea de {nome_alvo}")
        ti = st.slider("Escolha o instante (t)", 0.0, float(t_max), float(t_max/2))
        
        ci = np.interp(ti, t, conc_alvo)
        ai_val = np.interp(ti, t, conc_a)
        bi_val = np.interp(ti, t, conc_b) if modelo == "A + B → Produto" else 0
        
        # v = k * [A]^na * [B]^nb
        vi = k * (ai_val**ordem_a) * (bi_val**ordem_b if modelo == "A + B → Produto" and ordem_b > 0 else 1)
        slope = -vi # A inclinação é negativa pois consome reagente
        
        # Cálculo da Equação da Reta
        b_coef = ci - slope * ti
        sinal_b = "+" if b_coef >= 0 else "-"
        
        # Pontos extremos da reta tangente
        dt_span = t_max * 0.15
        t_start = max(0, ti - dt_span)
        t_end = min(t_max, ti + dt_span)
        c_start = ci + slope * (t_start - ti)
        c_end = ci + slope * (t_end - ti)
        
        delta_c = c_end - c_start
        delta_t = t_end - t_start

        st.write(f"Use os pontos da **reta tangente** para encontrar o coeficiente angular ($m$) e a equação da reta para {nome_alvo}:")
        st.latex(rf"m = \frac{{\Delta {nome_alvo}}}{{\Delta t}} \quad \rightarrow \quad v_{{inst}} = -m")
        
        # Exibindo os Deltas
        st.info(f"**Dados da Reta Tangente no gráfico:**\n\n"
                f"$\\Delta {nome_alvo} = {delta_c:.3f}$ M\n\n"
                f"$\\Delta t = {delta_t:.3f}$ s")
        
        if st.button("Revelar Velocidade e Equação"):
            st.latex(rf"m = \frac{{{delta_c:.3f}}}{{{delta_t:.3f}}} = {slope:.4f}")
            st.success(rf"**Velocidade ($v = -m$):** {vi:.4f} M/s")
            
            st.write(f"**Equação da Reta Tangente para {nome_alvo}:**")
            st.latex(rf"{nome_alvo} = {slope:.4f} \cdot t {sinal_b} {abs(b_coef):.4f}")

    # Desenhar reta tangente (Só desenha se o alvo estiver visível)
    if mostrar_alvo:
        fig.add_trace(go.Scatter(
            x=[t_start, t_end], y=[c_start, c_end], 
            mode='lines', name='Tangente', 
            line=dict(color='cyan', width=2)
        ))
        fig.add_trace(go.Scatter(
            x=[ti], y=[ci], mode='markers', 
            name='Instante (t)', marker=dict(color='white', size=8)
        ))
        fig.add_trace(go.Scatter(
            x=[t_start, t_start, t_end], y=[c_start, c_end, c_end],
            mode='lines', showlegend=False,
            line=dict(color='cyan', dash='dot', width=1)
        ))

with col1:
    fig.update_layout(xaxis_title="Tempo (s)", yaxis_title="Concentração (M)", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)
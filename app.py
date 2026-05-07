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

# 🕵️ MODO INVESTIGAÇÃO (DESAFIO)
modo_desafio = st.sidebar.toggle("🕵️ Modo Investigação", key="TOGGLE_DESAFIO")

if modo_desafio:
    # Gera valores secretos se não existirem
    if 'misterio_k' not in st.session_state:
        st.session_state.misterio_k = round(np.random.uniform(0.1, 1.5), 2)
        st.session_state.misterio_ordem = int(np.random.choice([0, 1, 2]))
    
    st.sidebar.success("**Modo Ativado!**\nVá na aba de Linearização e descubra a Ordem e a constante 'k' desta substância.")
    
    if st.sidebar.button("🔄 Gerar Nova Substância"):
        st.session_state.misterio_k = round(np.random.uniform(0.1, 1.5), 2)
        st.session_state.misterio_ordem = int(np.random.choice([0, 1, 2]))
        st.rerun()
        
    modelo = "A → Produto" # Fixo para o desafio
    k_sid = st.session_state.misterio_k
    ordem_a_sid = st.session_state.misterio_ordem
    
    # Exibe apenas sliders básicos
    a0_sid = st.sidebar.slider("[A]₀ Inicial", 0.1, 5.0, 2.0, key="K4_A0_DES")
    t_max = st.sidebar.slider("Tempo Total", 10, 100, 50, key="K5_TMAX_DES")
else:
    # Controles Originais do Professor
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
# Cria uma máscara para manter apenas os dados onde a concentração dos reagentes é positiva.
# Usamos 1e-5 no lugar de 0 exato para garantir que não haja erros de log(0) na linearização.
limite_zero = 1e-5

if modelo == "A + B → Produto":
    # Se tiver B, a reação para quando A ou B acabarem
    indices_validos = (conc_a > limite_zero) & (conc_b > limite_zero)
else:
    # Se for só A, a reação para quando A acabar
    indices_validos = (conc_a > limite_zero)

# Aplicando o filtro para cortar as arrays de tempo e concentração
t = t[indices_validos]
conc_a = conc_a[indices_validos]
conc_b = conc_b[indices_validos]
conc_p = conc_p[indices_validos]

# --- Opções de Exibição ---
st.sidebar.divider()
st.sidebar.subheader("👁️ Exibir no gráfico?")
mostrar_a = st.sidebar.checkbox("Reagente [A]", value=True, key="K8_VIEW_A")
mostrar_b = st.sidebar.checkbox("Reagente [B]", value=True, key="K9_VIEW_B") if modelo == "A + B → Produto" else False
mostrar_p = st.sidebar.checkbox("Produto", value=True, key="K10_VIEW_P")

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

# -------------------------------------------------------------
# AS FERRAMENTAS MATEMÁTICAS COMPLETAS E DIDÁTICAS AQUI!
# -------------------------------------------------------------
if modo_calc == "Velocidade Média":
    with col2:
        st.subheader(f"Cálculo da Velocidade Média de {nome_alvo}")
        
        # Inputs de tempo
        t1 = st.number_input("Escolha t1", 0.0, float(t_max), min(5.0, float(t_max)), key="VM_T1")
        t2 = st.number_input("Escolha t2", 0.0, float(t_max), min(20.0, float(t_max)), key="VM_T2")
        
        # Cálculos de concentração (Interpolação)
        c1 = np.interp(t1, t, conc_alvo)
        c2 = np.interp(t2, t, conc_alvo)
        
        # Cálculo da velocidade
        v_media = abs(c2 - c1) / (t2 - t1) if t2 != t1 else 0
        
        st.latex(rf"v_m = \left| \frac{{\Delta {nome_alvo}}}{{\Delta t}} \right|")
        
        if st.button("Revelar Velocidade Média", key="K15_BTN_VM"):
            st.latex(rf"v_m = \frac{{|{c2:.3f} - {c1:.3f}|}}{{{t2} - {t1}}}")
            st.success(rf"**Resposta:** {v_media:.4f} M/s")
            
    # Desenho da Secante
    if mostrar_alvo: 
        fig_main.add_trace(go.Scatter(
            x=[t1, t2], y=[c1, c2], mode='markers+lines+text', name='Secante', 
            text=[f"{c1:.3f}M", f"{c2:.3f}M"], textposition=["bottom left", "top right"],
            textfont=dict(color="yellow", size=14), line=dict(color='yellow', dash='dash', width=2),
            marker=dict(size=10)
        ))

elif modo_calc == "Velocidade Instantânea":
    with col2:
        st.subheader(f"Cálculo da Velocidade Instantânea de {nome_alvo}")
        ti = st.slider("Escolha o instante (t)", 0.0, float(t_max), float(t_max/2), key="K16_VI_TI")
        
        ci = np.interp(ti, t, conc_alvo)
        ai_val = np.interp(ti, t, conc_a)
        bi_val = np.interp(ti, t, conc_b) if modelo == "A + B → Produto" else 0
        
        # Cálculo cinético real no ponto
        vi = k_sid * (ai_val**ordem_a_sid) * (bi_val**ordem_b_sid if modelo == "A + B → Produto" and ordem_b_sid > 0 else 1)
        slope = -vi # Inclinação negativa para reagentes
        b_coef = ci - slope * ti
        sinal_b = "+" if b_coef >= 0 else "-"
        
     # Geometria da Reta Tangente: Calculando Interceptos nos Eixos
        if slope != 0:
            # Ponto que toca o eixo Y (t = 0)
            t_int_y = 0.0
            c_int_y = b_coef
            
            # Ponto que toca o eixo X (y = 0) -> 0 = slope * t + b_coef
            t_int_x = -b_coef / slope
            c_int_x = 0.0
        else:
            t_int_y, c_int_y = 0.0, ci
            t_int_x, c_int_x = t_max, ci

        # Limitando a reta para NÃO ter Y negativo
        if slope < 0: 
            # Reagentes (decrescente): a reta vai do eixo Y ao eixo X
            t_start, c_start = t_int_y, c_int_y
            t_end, c_end = t_int_x, c_int_x
        else: 
            # Produtos (crescente): começa no eixo X (ou zero) e vai até o fim do gráfico
            t_start = max(0.0, t_int_x)
            c_start = slope * t_start + b_coef
            t_end = t_max
            c_end = slope * t_end + b_coef

        delta_c = c_end - c_start
        delta_t = t_end - t_start
        
        st.write(f"Use os pontos da **reta tangente** para encontrar $m$ e a equação da reta para {nome_alvo}:")
        st.latex(rf"m = \frac{{\Delta {nome_alvo}}}{{\Delta t}} \quad \rightarrow \quad v_{{inst}} = -m")
        
        # Quadro de informações dos Deltas
        st.info(f"**Dados da Reta Tangente no gráfico:**\n\n$\\Delta {nome_alvo} = {delta_c:.3f}$ M\n\n$\\Delta t = {delta_t:.3f}$ s")
        
        if st.button("Revelar Velocidade e Equação", key="K17_BTN_VI"):
            st.latex(rf"m = \frac{{{delta_c:.3f}}}{{{delta_t:.3f}}} = {slope:.4f}")
            st.success(rf"**Velocidade ($v = -m$):** {vi:.4f} M/s")
            st.write(f"**Equação da Reta Tangente:**")
            st.latex(rf"{nome_alvo} = {slope:.4f} \cdot t {sinal_b} {abs(b_coef):.4f}")
            
    # Desenho da Reta Tangente e do Triângulo Tracejado
    if mostrar_alvo:
        # 1. A reta tangente restrita aos eixos
        fig_main.add_trace(go.Scatter(x=[t_start, t_end], y=[c_start, c_end], mode='lines', name='Tangente', line=dict(color='cyan', width=2)))
        
        # 2. Ponto do instante selecionado (t)
        fig_main.add_trace(go.Scatter(x=[ti], y=[ci], mode='markers', name='Instante (t)', marker=dict(color='White', size=10, symbol='circle', line=dict(color='black', width=2))))
        
        # 3. Triângulo tracejado para os deltas (opcional, formando ângulo reto)
        fig_main.add_trace(go.Scatter(x=[t_start, t_start, t_end], y=[c_start, c_end, c_end], mode='lines', showlegend=False, line=dict(color='cyan', dash='dot', width=2)))

        # 4. MARCAÇÃO DOS 2 PONTOS QUE TOCAM OS EIXOS (com valores em X e Y)
        if slope < 0:
            fig_main.add_trace(go.Scatter(
                x=[t_int_y, t_int_x], 
                y=[c_int_y, c_int_x], 
                mode='markers+text', 
                name='Interceptos',
                text=[f"(0.00, {c_int_y:.2f} M)", f"({t_int_x:.2f} s, 0.00)"],
                textposition=["top right", "top right"],
                marker=dict(color='yellow', size=10, symbol='x')
            ))
        elif slope > 0 and t_int_x >= 0: # Caso analise um Produto
            fig_main.add_trace(go.Scatter(
                x=[t_int_x], 
                y=[c_int_x], 
                mode='markers+text', 
                name='Intercepto X',
                text=[f"({t_int_x:.2f} s, 0.00)"],
                textposition="top left",
                marker=dict(color='yellow', size=10, symbol='x')
            ))
# -------------------------------------------------------------

with col1:
    fig_main.update_layout(xaxis_title="Tempo (s)", yaxis_title="Molaridade (M)", template="plotly_dark")
    st.plotly_chart(fig_main, use_container_width=True, key="CHART_1_PRINCIPAL")

# --- 2. Linearização ---
st.divider()
st.subheader(f"📈 Linearização para {nome_alvo}")

# Dividimos a tela: Gráfico na esquerda (c_l1) e Ferramenta na direita (c_l2)
c_l1, c_l2 = st.columns([2, 1])

# 1. Prepara os dados do eixo Y com base na ordem atual
if ordem_alvo == 0: 
    y_lin, lab_lin = conc_alvo, nome_alvo
elif ordem_alvo == 1: 
    y_lin, lab_lin = np.log(conc_alvo + 1e-9), f"ln({nome_alvo})"
else: 
    y_lin, lab_lin = 1/(conc_alvo + 1e-9), f"1/{nome_alvo}"

# Cria o gráfico de linha (laranja)
fig_lin = go.Figure(go.Scatter(x=t, y=y_lin, name="Linearização", line=dict(color='orange', width=2)))

with c_l2:
    st.write("### Encontre a Constante $k$")
    st.write("A inclinação ($m$) desta reta corresponde ao valor de **k**!")
    
  # --- AJUSTE DA BASE TEMPORAL DA RETA ---
    # Descobre qual foi o último segundo real antes de o reagente acabar
    t_real_max = float(t[-1]) 
    
    # 1. Os inputs travados para garantir que os pontos caiam exatamente DENTRO da reta
    t1_lin = st.number_input("Escolha t1", 0.0, t_real_max, min(1.0, t_real_max/4), key="LIN_T1")
    t2_lin = st.number_input("Escolha t2", 0.0, t_real_max, min(5.0, t_real_max/2), key="LIN_T2")
    
    # 2. As linhas de cálculo (MANTENHA O MESMO ALINHAMENTO)
    y1_lin = np.interp(t1_lin, t, y_lin)
    y2_lin = np.interp(t2_lin, t, y_lin)
    
    # 3. O cálculo do coeficiente
    m_lin = (y2_lin - y1_lin) / (t2_lin - t1_lin) if t2_lin != t1_lin else 0
    
    # Define a regra do sinal baseada na ordem
    if ordem_alvo == 0 or ordem_alvo == 1:
        k_calculado = -m_lin
        formula_k = "k = -m"
    else:
        k_calculado = m_lin
        formula_k = "k = m"
        
    st.latex(rf"m = \frac{{\Delta y}}{{\Delta x}} \quad \rightarrow \quad {formula_k}")
    
    if st.button("Calcular $k$ pelo Gráfico", key="K25_BTN_LIN"):
        st.latex(rf"m = \frac{{{y2_lin:.3f} - ({y1_lin:.3f})}}{{{t2_lin} - {t1_lin}}}")
        st.success(rf"**Constante $k$ calculada:** {k_calculado:.4f}")

# 3. Plota o Gráfico na coluna da esquerda
with c_l1:
    # Adiciona os pontos "X" brancos no gráfico para mostrar onde o aluno está medindo
    fig_lin.add_trace(go.Scatter(
        x=[t1_lin, t2_lin], y=[y1_lin, y2_lin], mode='markers+text', name='Pontos de Medição',
        text=[f"y={y1_lin:.2f}", f"y={y2_lin:.2f}"], textposition="top right",
        marker=dict(color='white', size=10, symbol='x')
    ))
    # O comando xaxis=dict(range=[0, t_real_max]) dá o zoom perfeito na reta
    fig_lin.update_layout(
        height=350, 
        template="plotly_dark", 
        yaxis_title=lab_lin, 
        xaxis_title="Tempo (s)",
        xaxis=dict(range=[0, t_real_max]) 
    )
    st.plotly_chart(fig_lin, use_container_width=True, key="CHART_2_LINEAR")

# --- 3. Comparador Histórico ---
st.divider()
st.header("📚 Comparador de Curvas Cinéticas")
if 'historico' not in st.session_state: st.session_state.historico = []

h1, h2, h3 = st.columns(3)
with h1: n_comp = st.number_input("Ordem", 0.0, 3.0, 1.0, step=0.5, key="K18_HIST_N")
with h2: c_comp = st.number_input("[A]₀", 0.1, 10.0, 2.0, key="K19_HIST_C")
with h3: k_comp = st.number_input("k", 0.01, 5.0, 0.45, key="K20_HIST_K")

bg, br = st.columns(2)
with bg:
    if st.button("🚀 Gravar Curva", key="K21_BTN_GRAVAR"):
        tc = np.linspace(0, t_max, 1000)
        sc = odeint(lambda y, t, k, n: [-k*(y[0]**n)], [c_comp], tc, args=(k_comp, n_comp))
        
        # --- Legenda formatada e organizada ---
        legenda_organizada = f"Ordem: {n_comp}  |  [A]₀: {c_comp:.2f}  |  k: {k_comp:.2f}"
        
        st.session_state.historico.append({'t': tc, 'y': sc[:, 0], 'label': legenda_organizada})
with br:
    if st.button("🗑️ Resetar Histórico", key="K22_BTN_RESET"):
        st.session_state.historico = []
        st.rerun()

fig_h = go.Figure()
if not st.session_state.historico:
    fig_h.add_annotation(text="Adicione curvas para comparar", showarrow=False)
else:
    for c in st.session_state.historico:
        fig_h.add_trace(go.Scatter(x=c['t'], y=c['y'], name=c['label'], mode='lines'))

fig_h.update_layout(xaxis=dict(title="Tempo (s)", range=[0, 15]), yaxis=dict(title="Conc. [A]", range=[0, 6]), height=450, template="plotly_dark")
st.plotly_chart(fig_h, use_container_width=True, key="CHART_3_HISTORICO")

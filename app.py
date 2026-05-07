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
limite_zero = 1e-5
if modelo == "A + B → Produto":
    indices_validos = (conc_a > limite_zero) & (conc_b > limite_zero)
else:
    indices_validos = (conc_a > limite_zero)

t = t[indices_validos]
conc_a = conc_a[indices_validos]
if modelo == "A + B → Produto":
    conc_b = conc_b[indices_validos]
conc_p = conc_p[indices_validos]


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

# --- Lógica Visual de Meia-Vida (t½) ---
if mostrar_meia_vida and modelo == "A → Produto":
    c_atual = a0_sid
    t_atual = 0.0
    
    for i in range(1, 5): 
        if ordem_a_sid == 0: 
            t_meia = c_atual / (2 * k_sid) if k_sid != 0 else float('inf')
        elif ordem_a_sid == 1: 
            t_meia = np.log(2) / k_sid if k_sid != 0 else float('inf')
        elif ordem_a_sid == 2: 
            t_meia = 1 / (k_sid * c_atual) if (k_sid != 0 and c_atual != 0) else float('inf')
        else: 
            break
            
        t_atual += t_meia
        c_atual /= 2
        
        if t_atual > t_max: 
            break 
            
        fig_main.add_shape(type="line", x0=t_atual, x1=t_atual, y0=0, y1=c_atual, line=dict(color="orange", width=1, dash="dot"))
        fig_main.add_shape(type="line", x0=0, x1=t_atual, y0=c_atual, y1=c_atual, line=dict(color="orange", width=1, dash="dot"))
        fig_main.add_trace(go.Scatter(
            x=[t_atual], y=[c_atual], 
            mode='markers+text', 
            name=f'{i}º t½', 
            text=[f"{t_atual:.1f}s"], 
            textposition="top right",
            textfont=dict(color="orange"),
            marker=dict(color='orange', size=8, symbol='diamond')
        ))

# -------------------------------------------------------------
if modo_calc == "Velocidade Média":
    with col2:
        st.subheader(f"Cálculo da Velocidade Média de {nome_alvo}")
        
        # --- AJUSTE DA BASE TEMPORAL ---
        t_limite = float(t[-1])
        t1 = st.number_input("Escolha t1", 0.0, t_limite, min(1.0, t_limite/4), key="VM_T1")
        t2 = st.number_input("Escolha t2", 0.0, t_limite, min(5.0, t_limite/2), key="VM_T2")
        
        c1 = np.interp(t1, t, conc_alvo)
        c2 = np.interp(t2, t, conc_alvo)
        
        v_media = abs(c2 - c1) / (t2 - t1) if t2 != t1 else 0
        
        st.latex(rf"v_m = \left| \frac{{\Delta {nome_alvo}}}{{\Delta t}} \right|")
        
        if st.button("Revelar Velocidade Média", key="K15_BTN_VM"):
            st.latex(rf"v_m = \frac{{|{c2:.3f} - {c1:.3f}|}}{{{t2} - {t1}}}")
            st.success(rf"**Resposta:** {v_media:.4f} M/s")
            
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
        
        # --- AJUSTE DA BASE TEMPORAL ---
        t_limite = float(t[-1])
        ti = st.slider("Escolha o instante (t)", 0.0, t_limite, float(t_limite/2), key="K16_VI_TI")
        
        ci = np.interp(ti, t, conc_alvo)
        ai_val = np.interp(ti, t, conc_a)
        bi_val = np.interp(ti, t, conc_b) if modelo == "A + B → Produto" else 0
        
        vi = k_sid * (ai_val**ordem_a_sid) * (bi_val**ordem_b_sid if modelo == "A + B → Produto" and ordem_b_sid > 0 else 1)
        slope = -vi 
        b_coef = ci - slope * ti
        sinal_b = "+" if b_coef >= 0 else "-"
        
        # Geometria da Reta Tangente: Calculando Interceptos nos Eixos
        if slope != 0:
            t_int_y = 0.0
            c_int_y = b_coef
            t_int_x = -b_coef / slope
            c_int_x = 0.0
        else:
            t_int_y, c_int_y = 0.0, ci
            t_int_x, c_int_x = t_max, ci

        # Limitando a reta para NÃO ter Y negativo
        if slope < 0: 
            t_start, c_start = t_int_y, c_int_y
            t_end, c_end = t_int_x, c_int_x
        else: 
            t_start = max(0.0, t_int_x)
            c_start = slope * t_start + b_coef
            t_end = t_max
            c_end = slope * t_end + b_coef

        delta_c = c_end - c_start
        delta_t = t_end - t_start
        
        st.write(f"Use os pontos da **reta tangente** para encontrar $m$ e a equação da reta para {nome_alvo}:")
        st.latex(rf"m = \frac{{\Delta {nome_alvo}}}{{\Delta t}} \quad \rightarrow \quad v_{{inst}} = -m")
        
        st.info(f"**Dados da Reta Tangente no gráfico:**\n\n$\\Delta {nome_alvo} = {delta_c:.3f}$ M\n\n$\\Delta t = {delta_t:.3f}$ s")
        
        if st.button("Revelar Velocidade e Equação", key="K17_BTN_VI"):
            st.latex(rf"m = \frac{{{delta_c:.3f}}}{{{delta_t:.3f}}} = {slope:.4f}")
            st.success(rf"**Velocidade ($v = -m$):** {vi:.4f} M/s")
            st.write(f"**Equação da Reta Tangente:**")
            st.latex(rf"{nome_alvo} = {slope:.4f} \cdot t {sinal_b} {abs(b_coef):.4f}")
            
        if st.button(f"📥 Salvar Ponto da Tangente", key="BTN_COLETAR_PONTO"):
            if 'pontos_taxa' not in st.session_state: 
                st.session_state.pontos_taxa = []
            st.session_state.pontos_taxa.append({'[C]': float(ci), 'Velocidade': float(vi)})
            
    if mostrar_alvo:
        fig_main.add_trace(go.Scatter(x=[t_start, t_end], y=[c_start, c_end], mode='lines', name='Tangente', line=dict(color='cyan', width=2)))
        fig_main.add_trace(

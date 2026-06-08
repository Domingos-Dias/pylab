import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import sympy as sp
from scipy.optimize import curve_fit
from sklearn.metrics import r2_score

# 1. Configuração da Página
st.set_page_config(page_title="Ajuste de Curvas", page_icon="📈", layout="wide")
st.title("📈 Ajuste de Curvas (Regressão Não Linear)")
st.markdown("Entre com as coordenadas, defina seu modelo matemático livremente e otimize os parâmetros.")

# Layout em colunas
col_dados, col_modelo = st.columns([1, 2])

# ==============================================================================
# COLUNA ESQUERDA: ENTRADA DE DADOS
# ==============================================================================
with col_dados:
    st.header("1. Coordenadas")
    
    # Define o tamanho inicial do array
    num_pontos = st.number_input("Número inicial de pontos:", min_value=2, max_value=1000, value=5, step=1)
    
    st.caption("Preencha as coordenadas X e Y abaixo. Você pode adicionar ou remover linhas clicando na tabela.")
    
    # Inicia um DataFrame vazio com o número de linhas escolhido
    df_inicial = pd.DataFrame({
        'X': np.zeros(num_pontos),
        'Y': np.zeros(num_pontos)
    })
    
    # Tabela de edição dinâmica do Streamlit
    df_editado = st.data_editor(
        df_inicial, 
        num_rows="dynamic", # Permite ao usuário adicionar/deletar linhas
        use_container_width=True,
        hide_index=False
    )

# ==============================================================================
# COLUNA DIREITA: MODELO E RESULTADOS
# ==============================================================================
with col_modelo:
    st.header("2. Modelo Matemático")
    
    # Entrada da equação genérica
    equacao_str = st.text_input(
        "Digite a equação paramétrica (ex: a * (x + b)**c):", 
        value="a * (x + b)**c"
    )

    try:
        # Tenta interpretar o texto como uma expressão matemática
        expr = sp.sympify(equacao_str)
        simbolos = sorted(list(expr.free_symbols), key=lambda s: s.name)
        
        if not simbolos:
            st.warning("Nenhuma variável ou parâmetro detectado na equação.")
            st.stop()

        # O usuário define qual letra representa a variável X do eixo
        nomes_simbolos = [s.name for s in simbolos]
        var_x_name = st.selectbox(
            "Qual dessas letras representa a variável independente (Eixo X)?", 
            nomes_simbolos, 
            index=nomes_simbolos.index('x') if 'x' in nomes_simbolos else 0
        )
        
        # Separa a variável independente dos parâmetros de otimização
        var_x = sp.Symbol(var_x_name)
        parametros = [s for s in simbolos if s.name != var_x_name]
        
        st.markdown(f"**Parâmetros identificados para ajuste:** `{(', '.join([p.name for p in parametros]))}`")
        
        # --- CHUTES INICIAIS (GERADOS DINAMICAMENTE) ---
        st.subheader("Chutes Iniciais (p0)")
        p0_guess = []
        
        # Cria colunas lado a lado baseadas na quantidade de parâmetros encontrados
        cols_p0 = st.columns(len(parametros))
        for i, p in enumerate(parametros):
            with cols_p0[i]:
                val = st.number_input(f"Valor inicial '{p.name}':", value=1.0, format="%.4f")
                p0_guess.append(val)
                
        # --- BOTÃO DE CÁLCULO ---
        if st.button("Calcular Regressão", type="primary", use_container_width=True):
            
            x_data = df_editado['X'].values
            y_data = df_editado['Y'].values
            
            # Verifica se não há valores nulos ou vazios no Grid
            if len(x_data) < len(parametros):
                st.error(f"Erro: O número de pontos fornecidos ({len(x_data)}) deve ser maior ou igual ao número de parâmetros ({len(parametros)}).")
                st.stop()

            # Transforma a expressão abstrata do SymPy em uma função NumPy de alta velocidade
            func_numerica = sp.lambdify([var_x] + parametros, expr, "numpy")
            
            # Encapsula para o formato que o curve_fit exige: f(x, p1, p2, ...)
            def modelo_para_scipy(x_val, *args):
                return func_numerica(x_val, *args)
                
            with st.spinner("Otimizando parâmetros..."):
                # Otimização
                popt, pcov = curve_fit(modelo_para_scipy, x_data, y_data, p0=p0_guess, maxfev=50000)
                y_pred = modelo_para_scipy(x_data, *popt)
                r2 = r2_score(y_data, y_pred)
                
                # --- RESULTADOS NUMÉRICOS ---
                st.success("Convergência alcançada!")
                
                res_cols = st.columns(len(parametros) + 1)
                for i, (p, val) in enumerate(zip(parametros, popt)):
                    with res_cols[i]:
                        st.metric(label=f"Parâmetro {p.name}", value=f"{val:.5f}")
                with res_cols[-1]:
                    st.metric(label="R² (Score)", value=f"{r2:.5f}")
                
                # --- EXIBIÇÃO DA EQUAÇÃO FINAL COM LATEX ---
                # Substitui os símbolos pelos números reais encontrados e gera o LaTeX
                expr_substituida = expr.subs({p: round(val, 5) for p, val in zip(parametros, popt)})
                st.latex(f"Y = {sp.latex(expr_substituida)}")
                
                # --- PLOTAGEM DO GRÁFICO (MATPLOTLIB) ---
                fig, ax = plt.subplots(figsize=(10, 5))
                
                # Dados reais
                ax.scatter(x_data, y_data, color='red', label='Dados Observados (Input)')
                
                # Curva do Modelo (500 pontos para ficar suave)
                margem = (max(x_data) - min(x_data)) * 0.1
                x_smooth = np.linspace(min(x_data) - margem, max(x_data) + margem, 500)
                y_smooth = modelo_para_scipy(x_smooth, *popt)
                
                ax.plot(x_smooth, y_smooth, color='blue', linewidth=2, label='Curva Ajustada (Modelo)')
                
                ax.set_xlabel(f"Eixo X ({var_x_name})")
                ax.set_ylabel("Eixo Y")
                ax.set_title(f"Ajuste de Curva (R² = {r2:.4f})")
                ax.legend()
                ax.grid(True, linestyle='--', alpha=0.6)
                
                # Exibe o gráfico gerado na interface do Streamlit
                st.pyplot(fig)

    except Exception as e:
        st.error(f"Não foi possível processar a equação ou o cálculo numérico.\nMotivo: {e}")
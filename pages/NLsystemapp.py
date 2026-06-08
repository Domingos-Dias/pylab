import streamlit as st
import sympy as sp
import numpy as np
from scipy.optimize import least_squares

# 1. Configuração inicial da página web
st.set_page_config(page_title="Solver Não Linear", page_icon="⚙️", layout="wide")

st.title("⚙️ Solver Reativo de Sistemas Não Lineares")
st.markdown("Resolva sistemas complexos e armazene variáveis na memória da calculadora.")

# Dicionário de memória (passará os valores da direita para a esquerda)
constantes_calculadora = {}

# 2. Layout em Colunas (No PC ficam lado a lado, no Celular ficam empilhadas)
col_solver, col_calc = st.columns(2)

# ==========================================
# PAINEL DIREITO (CALCULADORA)
# ==========================================
with col_calc:
    st.header("🧮 Memória & Calculadora")
    st.caption("Crie constantes (ex: `k1 = 5*2`) ou faça contas isoladas.")
    
    # Caixa de texto padrão do Streamlit (múltiplas linhas)
    calc_texto = st.text_area("Entrada da Calculadora (Aperte Ctrl+Enter para processar):", height=200, key="calc_input")
    
    # --- NOVO: Controle de casas decimais específico para os valores calculados ---
    casas_calc = st.number_input("Casas Decimais (Calculadora):", min_value=0, max_value=15, value=6, step=1, key="casas_calc")
    
    st.subheader("Valores Calculados:")
    
    resultados_calc = []
    if calc_texto.strip():
        linhas = calc_texto.split('\n')
        for linha in linhas:
            linha_limpa = linha.strip()
            if not linha_limpa:
                resultados_calc.append("")
                continue
            
            try:
                if "=" in linha_limpa:
                    var_nome, expressao = linha_limpa.split("=", 1)
                    var_nome = var_nome.strip()
                    
                    if not var_nome.isidentifier():
                        resultados_calc.append("Erro: Nome inválido")
                        continue
                        
                    expr = sp.sympify(expressao).subs(constantes_calculadora)
                    
                    if expr.free_symbols:
                        resultados_calc.append("Erro: Falta variável")
                    else:
                        val = float(expr.evalf())
                        constantes_calculadora[var_nome] = val # Guarda na memória em precisão total
                        
                        # Aplica a quantidade de casas decimais escolhida pelo usuário
                        str_val = f"{val:.{casas_calc}f}"
                        resultados_calc.append(f"{var_nome} = {str_val}")
                else:
                    expr = sp.sympify(linha_limpa).subs(constantes_calculadora)
                    if expr.free_symbols:
                        resultados_calc.append("Erro: Falta variável")
                    else:
                        val = float(expr.evalf())
                        str_val = f"{val:.{casas_calc}f}"
                        resultados_calc.append(str_val)
            except Exception:
                resultados_calc.append("...")
                
        # Exibe em um bloco copiável nativo
        st.code("\n".join(resultados_calc), language="text")
    else:
        st.code("--", language="text")

# ==========================================
# PAINEL ESQUERDO (SOLVER)
# ==========================================
with col_solver:
    st.header("⚙️ Solver Principal")
    st.caption("Digite as equações (uma por linha). O sistema aceita `=` diretamente!")
    
    # Caixa de texto padrão do Streamlit
    eq_texto = st.text_area("Equações do Sistema (Aperte Ctrl+Enter para processar):", height=200, key="eq_input")
    
    # Painel de Configurações
    col_cfg1, col_cfg2 = st.columns(2)
    with col_cfg1:
        mult = st.number_input("Multiplicador do Resultado:", value=1.0, format="%.4f")
    with col_cfg2:
        casas = st.number_input("Casas Decimais:", min_value=0, max_value=15, value=5, step=1)
        
    st.subheader("Resultados:")
    
    if not eq_texto.strip():
        st.info("Aguardando entrada na caixa acima...")
    else:
        linhas = [linha.strip() for linha in eq_texto.split('\n') if linha.strip()]
        
        try:
            expressoes = []
            simbolos_set = set()
            
            for linha in linhas:
                if "=" in linha:
                    lado_esq, lado_dir = merge = linha.split("=", 1)
                    expr = sp.sympify(lado_esq) - sp.sympify(lado_dir)
                else:
                    expr = sp.sympify(linha)
                    
                # Substitui as constantes da calculadora
                expr = expr.subs(constantes_calculadora)
                
                expressoes.append(expr)
                simbolos_set.update(expr.free_symbols)
                
            simbolos = sorted(list(simbolos_set), key=lambda s: s.name)
            num_eqs = len(expressoes)
            num_vars = len(simbolos)
            
            if num_vars == 0:
                st.warning("Nenhuma variável detectada.")
            elif num_eqs != num_vars:
                st.warning(f"Sistema não resolvível ({num_eqs} eq, {num_vars} incógnitas). Precisa ser quadrado.")
            else:
                func_numerica = sp.lambdify(simbolos, expressoes, "numpy")
                
                def sistema_para_scipy(valores_vars):
                    return func_numerica(*valores_vars)
                    
                chute_inicial = np.full(num_vars, 0.1) 
                
                limite_inferior = np.full(num_vars, 0.0) 
                limites = (limite_inferior, np.inf)
                
                with st.spinner("Calculando sistema..."):
                    resultado = least_squares(
                        sistema_para_scipy, 
                        chute_inicial, 
                        bounds=limites,
                        ftol=1e-10, xtol=1e-10, gtol=1e-10
                    )
                    
                    erro_maximo = np.max(np.abs(resultado.fun))
                    
                    if resultado.success and erro_maximo < 1e-5:
                        st.success("Sistema quadrado válido! Convergência alcançada.")
                        
                        # --- NOVO: Lógica de exibição da tag do multiplicador ---
                        if mult != 1.0:
                            # Limpa formatações feias como 1000.0000 para ficar apenas 1000
                            mult_limpo = f"{mult:.4f}".rstrip('0').rstrip('.')
                            suffix = f" (x{mult_limpo})"
                        else:
                            suffix = ""
                            
                        resultado_texto = "\n".join([f"{simb.name} = {(valor * mult):.{casas}f}{suffix}" for simb, valor in zip(simbolos, resultado.x)])
                        st.code(resultado_texto, language="text")
                    else:
                        st.error("Sem convergência real (Raízes negativas/complexas ou erro matemático).")
                        
        except Exception as e:
            st.info("Digitando... (aguardando sintaxe válida)")
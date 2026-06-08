import streamlit as st
import sympy as sp
import numpy as np
from scipy.optimize import least_squares

# 1. Configuração inicial da página web
st.set_page_config(page_title="Solver Não Linear", page_icon="⚙️", layout="wide")

st.title("⚙️ Solver Reativo de Sistemas Não Lineares")
st.markdown("Resolva sistemas complexos e armazene variáveis na memória da calculadora.")

constantes_calculadora = {}

# 2. Layout em Colunas 
col_solver, col_calc = st.columns(2)

# ==========================================
# PAINEL DIREITO (CALCULADORA)
# ==========================================
with col_calc:
    st.header("🧮 Memória & Calculadora")
    st.caption("Crie constantes (ex: `k1 = 5*2`) ou faça contas isoladas.")
    
    calc_texto = st.text_area("Entrada da Calculadora (Aperte Ctrl+Enter para processar):", height=200, key="calc_input")
    
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
                        constantes_calculadora[var_nome] = val 
                        
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
                
        st.code("\n".join(resultados_calc), language="text")
    else:
        st.code("--", language="text")

# ==========================================
# PAINEL ESQUERDO (SOLVER)
# ==========================================
with col_solver:
    st.header("⚙️ Solver Principal")
    st.caption("Digite as equações (uma por linha). O sistema aceita `=` diretamente!")
    
    eq_texto = st.text_area("Equações do Sistema (Aperte Ctrl+Enter para processar):", height=200, key="eq_input")
    
    # Painel de Configurações Expandido
    col_cfg1, col_cfg2, col_cfg3 = st.columns(3)
    with col_cfg1:
        mult = st.number_input("Multiplicador:", value=1.0, format="%.4f")
    with col_cfg2:
        casas = st.number_input("Casas Decimais:", min_value=0, max_value=15, value=5, step=1)
    with col_cfg3:
        # NOVO: Controle sobre a tolerância de rejeição de erros do algoritmo
        tol_erro = st.number_input("Tolerância (Erro):", value=0.00001, format="%.5f")
        
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
                    lado_esq, lado_dir = linha.split("=", 1)
                    expr = sp.sympify(lado_esq) - sp.sympify(lado_dir)
                else:
                    expr = sp.sympify(linha)
                    
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
                    
                limite_inferior = np.full(num_vars, 0.0) 
                limites = (limite_inferior, np.inf)
                
                # --- NOVO: Estratégia Multi-Start para fugir de gradientes planos ---
                chutes_para_testar = [0.1, 1.0, 0.01, 2.0, 5.0]
                sucesso_real = False
                resultado_final = None
                melhor_erro_encontrado = float('inf')
                
                with st.spinner("Calculando sistema..."):
                    for chute_base in chutes_para_testar:
                        chute_inicial = np.full(num_vars, chute_base)
                        resultado = least_squares(
                            sistema_para_scipy, 
                            chute_inicial, 
                            bounds=limites,
                            ftol=1e-10, xtol=1e-10, gtol=1e-10
                        )
                        
                        erro_maximo = np.max(np.abs(resultado.fun))
                        
                        # Guarda o menor erro caso todas as tentativas falhem
                        if erro_maximo < melhor_erro_encontrado:
                            melhor_erro_encontrado = erro_maximo
                            resultado_final = resultado
                        
                        # Se achou uma solução que respeita a nossa tolerância, interrompe a busca!
                        if resultado.success and erro_maximo <= tol_erro:
                            sucesso_real = True
                            break
                    
                    # Exibição dos resultados baseada na estratégia acima
                    if sucesso_real:
                        st.success("Sistema quadrado válido! Convergência alcançada.")
                        
                        if mult != 1.0:
                            mult_limpo = f"{mult:.4f}".rstrip('0').rstrip('.')
                            suffix = f" (x{mult_limpo})"
                        else:
                            suffix = ""
                            
                        resultado_texto = "\n".join([f"{simb.name} = {(valor * mult):.{casas}f}{suffix}" for simb, valor in zip(simbolos, resultado_final.x)])
                        st.code(resultado_texto, language="text")
                    else:
                        st.error(f"Sem convergência. Menor erro residual atingido: {melhor_erro_encontrado:.5f}")
                        st.caption("Dica: Tente aumentar um pouco a Tolerância (Erro) ou verifique se as raízes são reais e positivas.")
                        
        except Exception as e:
            st.info("Digitando... (aguardando sintaxe válida)")
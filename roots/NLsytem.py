import tkinter as tk
import sympy as sp
import numpy as np
from scipy.optimize import least_squares

class NonLinearSolverApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Solver Reativo - Sistemas Não Lineares & Calculadora")
        self.root.geometry("1100x750")
        self.root.resizable(True, True) 
        
        # Dicionário de memória para as constantes da calculadora
        self.constantes_calculadora = {}

        # --- DIVISOR DE TELA (PanedWindow) ---
        self.paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=6)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # ==========================================
        # PAINEL ESQUERDO: O SOLVER PRINCIPAL
        # ==========================================
        self.solver_frame = tk.Frame(self.paned)
        self.paned.add(self.solver_frame, minsize=650)

        tk.Label(
            self.solver_frame, 
            text="⚙️ SOLVER DE SISTEMAS\nDigite as equações (uma por linha). O sistema aceita '=' diretamente!",
            font=("Arial", 10, "bold")
        ).pack(pady=(0, 10))

        self.text_input = tk.Text(self.solver_frame, height=12, width=60, font=("Courier", 12))
        self.text_input.pack(pady=5)
        self.text_input.bind("<KeyRelease>", self.processar_equacoes)

        # --- 📐 PAINEL DE DIMENSÕES DA CAIXA DE TEXTO ---
        ui_frame = tk.LabelFrame(self.solver_frame, text=" Tamanho da Área de Digitação ", padx=10, pady=5)
        ui_frame.pack(fill=tk.X, pady=5)

        tk.Label(ui_frame, text="Linhas:").grid(row=0, column=0, sticky="w", padx=5)
        self.scale_height = tk.Scale(ui_frame, from_=5, to=150, orient=tk.HORIZONTAL, length=180, command=self.atualizar_tamanho)
        self.scale_height.set(12)
        self.scale_height.grid(row=0, column=1, padx=5)

        tk.Label(ui_frame, text="Caracteres:").grid(row=0, column=2, sticky="w", padx=15)
        self.scale_width = tk.Scale(ui_frame, from_=40, to=300, orient=tk.HORIZONTAL, length=180, command=self.atualizar_tamanho)
        self.scale_width.set(60)
        self.scale_width.grid(row=0, column=3, padx=5)

        # --- ⚙️ PAINEL DE CONFIGURAÇÕES DE EXIBIÇÃO ---
        config_frame = tk.LabelFrame(self.solver_frame, text=" Configurações do Resultado ", padx=10, pady=10)
        config_frame.pack(fill=tk.X, pady=10)

        tk.Label(config_frame, text="Multiplicador do Resultado Final:").grid(row=0, column=0, sticky="w", padx=5)
        self.mult_entry = tk.Entry(config_frame, width=10)
        self.mult_entry.insert(0, "1.0") 
        self.mult_entry.grid(row=0, column=1, padx=5, sticky="w")
        self.mult_entry.bind("<KeyRelease>", self.processar_equacoes)

        tk.Label(config_frame, text="Casas Decimais:").grid(row=1, column=0, sticky="w", padx=5, pady=(5,0))
        self.casas_spin = tk.Spinbox(config_frame, from_=1, to=15, width=8, command=self.processar_equacoes)
        self.casas_spin.delete(0, "end")
        self.casas_spin.insert(0, "5") 
        self.casas_spin.grid(row=1, column=1, padx=5, pady=(5,0), sticky="w")
        self.casas_spin.bind("<KeyRelease>", self.processar_equacoes)

        self.status_label = tk.Label(self.solver_frame, text="Status: Aguardando entrada...", fg="gray", font=("Arial", 10, "italic"))
        self.status_label.pack(pady=5)

        tk.Frame(self.solver_frame, height=2, bd=1, relief=tk.SUNKEN).pack(fill=tk.X, pady=10)

        tk.Label(self.solver_frame, text="Resultados:", font=("Arial", 12, "bold")).pack()
        
        self.result_text = tk.Text(
            self.solver_frame, height=10, width=50, font=("Courier", 14, "bold"), 
            fg="darkblue", bg=self.root.cget('bg'), bd=0, highlightthickness=0
        )
        self.result_text.pack(pady=10)
        self.result_text.insert("1.0", "--")
        self.result_text.config(state=tk.DISABLED)


        # ==========================================
        # PAINEL DIREITO: A CALCULADORA AUXILIAR
        # ==========================================
        self.calc_frame = tk.Frame(self.paned, padx=10)
        self.paned.add(self.calc_frame, minsize=300)

        tk.Label(
            self.calc_frame, 
            text="🧮 MEMÓRIA & CALCULADORA\nCrie constantes (ex: k1 = 5*2)\nou faça contas isoladas.",
            font=("Arial", 10, "bold"),
            fg="darkgreen"
        ).pack(pady=(0, 10))

        self.calc_input = tk.Text(self.calc_frame, height=12, width=30, font=("Courier", 12), bg="#f4fcf4")
        self.calc_input.pack(fill=tk.X, pady=5)
        self.calc_input.bind("<KeyRelease>", self.processar_calculadora)

        tk.Frame(self.calc_frame, height=2, bd=1, relief=tk.SUNKEN).pack(fill=tk.X, pady=10)

        tk.Label(self.calc_frame, text="Valores Calculados (Copie se quiser):", font=("Arial", 12, "bold"), fg="darkgreen").pack()
        
        self.calc_result_text = tk.Text(
            self.calc_frame, height=12, width=30, font=("Courier", 13, "bold"), 
            fg="darkgreen", bg=self.root.cget('bg'), bd=0, highlightthickness=0
        )
        self.calc_result_text.pack(fill=tk.BOTH, expand=True, pady=5)
        self.calc_result_text.insert("1.0", "--")
        self.calc_result_text.config(state=tk.DISABLED)


    # ==========================================
    # LÓGICA DO SISTEMA
    # ==========================================
    def atualizar_tamanho(self, event=None):
        try:
            h = self.scale_height.get()
            w = self.scale_width.get()
            self.text_input.config(height=h, width=w)
            self.calc_input.config(height=h) 
        except Exception:
            pass

    def atualizar_texto_copiavel(self, widget, texto):
        widget.config(state=tk.NORMAL) 
        widget.delete("1.0", tk.END)
        widget.insert("1.0", texto)
        widget.config(state=tk.DISABLED) 

    def processar_calculadora(self, event=None):
        texto = self.calc_input.get("1.0", tk.END).strip("\n")
        
        self.constantes_calculadora = {}
        
        if not texto.strip():
            self.atualizar_texto_copiavel(self.calc_result_text, "--")
            self.processar_equacoes() 
            return

        linhas = texto.split('\n')
        resultados = []

        for linha in linhas:
            linha_limpa = linha.strip()
            if not linha_limpa:
                resultados.append("")
                continue
            
            try:
                # Se for uma declaração de variável (ex: k1 = 10 * 2)
                if "=" in linha_limpa:
                    var_nome, expressao = linha_limpa.split("=", 1)
                    var_nome = var_nome.strip()
                    
                    if not var_nome.isidentifier():
                        resultados.append("Erro: Nome inválido")
                        continue
                        
                    expr = sp.sympify(expressao).subs(self.constantes_calculadora)
                    
                    if expr.free_symbols:
                        resultados.append("Erro: Falta variável")
                    else:
                        val = float(expr.evalf())
                        self.constantes_calculadora[var_nome] = val 
                        
                        str_val = f"{val:.6f}".rstrip('0').rstrip('.')
                        if str_val == "": str_val = "0"
                        
                        # --- MODIFICAÇÃO AQUI: Adiciona o nome da variável na exibição ---
                        resultados.append(f"{var_nome} = {str_val}")
                        
                # Se for só uma conta isolada
                else:
                    expr = sp.sympify(linha_limpa).subs(self.constantes_calculadora)
                    if expr.free_symbols:
                        resultados.append("Erro: Falta variável")
                    else:
                        val = float(expr.evalf())
                        str_val = f"{val:.6f}".rstrip('0').rstrip('.')
                        if str_val == "": str_val = "0"
                        resultados.append(str_val) # Conta isolada continua mostrando só o valor numérico
                        
            except Exception:
                resultados.append("...")

        self.atualizar_texto_copiavel(self.calc_result_text, "\n".join(resultados))
        self.processar_equacoes()

    def processar_equacoes(self, event=None):
        texto = self.text_input.get("1.0", tk.END).strip()
        
        if not texto:
            self.status_label.config(text="Status: Aguardando entrada...", fg="gray")
            self.atualizar_texto_copiavel(self.result_text, "--")
            return

        linhas = [linha.strip() for linha in texto.split('\n') if linha.strip()]

        try:
            mult = float(self.mult_entry.get())
        except ValueError:
            mult = 1.0 

        try:
            casas = int(self.casas_spin.get())
            casas = max(0, min(15, casas)) 
        except ValueError:
            casas = 5

        try:
            expressoes = []
            simbolos_set = set()
            
            for linha in linhas:
                if "=" in linha:
                    lado_esq, lado_dir = linha.split("=", 1)
                    expr = sp.sympify(lado_esq) - sp.sympify(lado_dir)
                else:
                    expr = sp.sympify(linha)
                    
                expr = expr.subs(self.constantes_calculadora)
                
                expressoes.append(expr)
                simbolos_set.update(expr.free_symbols)

            simbolos = sorted(list(simbolos_set), key=lambda s: s.name)
            num_eqs = len(expressoes)
            num_vars = len(simbolos)

            if num_vars == 0:
                return

            if num_eqs != num_vars:
                self.status_label.config(
                    text=f"Status: Sistema não resolvível ({num_eqs} eq, {num_vars} incógnitas). Precisa ser quadrado.", 
                    fg="orange"
                )
                self.atualizar_texto_copiavel(self.result_text, "--")
                return

            self.status_label.config(text="Status: Sistema quadrado válido! Calculando...", fg="green")

            func_numerica = sp.lambdify(simbolos, expressoes, "numpy")

            def sistema_para_scipy(valores_vars):
                return func_numerica(*valores_vars)

            chute_inicial = np.full(num_vars, 0.1) 
            limite_inferior = np.full(num_vars, 1e-5) 
            limites = (limite_inferior, np.inf)

            resultado = least_squares(sistema_para_scipy, chute_inicial, bounds=limites)

            if resultado.success:
                resultado_texto = "\n".join([f"{simb.name} = {(valor * mult):.{casas}f}" for simb, valor in zip(simbolos, resultado.x)])
                self.atualizar_texto_copiavel(self.result_text, resultado_texto)
            else:
                self.atualizar_texto_copiavel(self.result_text, "Sem convergência real\n(Limites excedidos ou erro matemático)")

        except Exception as e:
            self.status_label.config(text="Status: Digitando... (aguardando sintaxe válida)", fg="gray")
            self.atualizar_texto_copiavel(self.result_text, "--")

if __name__ == "__main__":
    root = tk.Tk()
    app = NonLinearSolverApp(root)
    root.mainloop()
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from sklearn.metrics import r2_score

# Bibliotecas para abrir a janela de seleção
import tkinter as tk
from tkinter import filedialog
import os

# ==============================================================================
# 1. CONFIGURAÇÃO DAS COLUNAS E MODELO
# ==============================================================================
# ATENÇÃO: Os nomes das colunas ainda precisam bater com o seu Excel.
NOME_Y = 'Vazao'
NOMES_X = ['Cota']


# Definição do Modelo Matemático
def modelo_matematico(X, a, b, c):
    var_x = X[0]
    return a * (var_x + b) ** c


p0_guess = [0.004, 10, 1.6]
formato_equacao = r"$Vazao = {0:.5f}(Cota + {1:.2f})^{{{2:.2f}}}$"

# ==============================================================================
# 2. SELEÇÃO DE ARQUIVO (Janela Windows/Mac)
# ==============================================================================
print("--> Aguardando seleção do arquivo...")

# Cria uma janela raiz oculta (para não abrir uma tela em branco do tkinter)
root = tk.Tk()
root.withdraw()

# Abre a janela de diálogo nativa
caminho_arquivo = filedialog.askopenfilename(
    title="Selecione o arquivo de dados (Excel ou CSV)",
    filetypes=[("Arquivos de Dados", "*.xlsx *.xls *.csv"), ("Todos os arquivos", "*.*")]
)

# Verifica se o usuário cancelou a seleção
if not caminho_arquivo:
    print("--> NENHUM ARQUIVO SELECIONADO. Encerrando.")
    exit()

print(f"--> Arquivo selecionado: {os.path.basename(caminho_arquivo)}")

# ==============================================================================
# 3. LEITURA DE DADOS (PANDAS)
# ==============================================================================
try:
    if caminho_arquivo.endswith('.csv'):
        df = pd.read_csv(caminho_arquivo)
    else:
        df = pd.read_excel(caminho_arquivo)

    # Verifica se as colunas existem
    colunas_necessarias = [NOME_Y] + NOMES_X
    if not all(col in df.columns for col in colunas_necessarias):
        print(f"\nERRO: O arquivo precisa ter as colunas: {colunas_necessarias}")
        print(f"Colunas encontradas: {list(df.columns)}")
        exit()

    # Prepara os dados
    y_data = df[NOME_Y].values
    X_data = [df[col].values for col in NOMES_X]

except Exception as e:
    print(f"Erro ao ler arquivo: {e}")
    exit()

# ==============================================================================
# 4. CÁLCULO E PLOTAGEM
# ==============================================================================
num_vars = len(X_data)

try:
    # Ajuste
    popt, pcov = curve_fit(modelo_matematico, X_data, y_data, p0=p0_guess, maxfev=20000)
    y_pred = modelo_matematico(X_data, *popt)
    r2 = r2_score(y_data, y_pred)
    texto_eq = formato_equacao.format(*popt)

    print("\n=== SUCESSO ===")
    print(f"Equação: {texto_eq}")
    print(f"R²: {r2:.5f}")

    # Plot
    plt.figure(figsize=(10, 6))


    # Função auxiliar para texto
    def add_text(ax, txt, r2_val):
        msg = f"Modelo:\n{txt}\n\n$R^2 = {r2_val:.4f}$"
        ax.text(0.05, 0.95, msg, transform=ax.transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))


    if num_vars == 1:
        x_val = X_data[0]
        x_smooth = np.linspace(min(x_val), max(x_val), 500)
        y_smooth = modelo_matematico([x_smooth], *popt)

        plt.scatter(x_val, y_data, color='red', label='Dados Reais')
        plt.plot(x_smooth, y_smooth, color='blue', linewidth=2, label='Ajuste')
        plt.xlabel(NOMES_X[0])
        plt.ylabel(NOME_Y)
    else:
        plt.scatter(y_data, y_pred, color='blue', alpha=0.6)
        vmin, vmax = min(y_data.min(), y_pred.min()), max(y_data.max(), y_pred.max())
        plt.plot([vmin, vmax], [vmin, vmax], 'r--', label='Ideal')
        plt.xlabel('Real')
        plt.ylabel('Calculado')

    ax = plt.gca()
    add_text(ax, texto_eq, r2)
    plt.title(f"Regressão - {os.path.basename(caminho_arquivo)}")
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.show()

except Exception as e:
    print(f"Erro no cálculo matemático: {e}")
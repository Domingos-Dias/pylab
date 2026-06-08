import streamlit as st

# Configuração da página inicial
st.set_page_config(
    page_title="Laboratório de Engenharia",
    page_icon="🧰",
    layout="centered"
)

# Título principal
st.title("🧰 Meu Canivete Suíço Matemático")

st.markdown("""
Bem-vindo ao seu repositório central de ferramentas matemáticas e de engenharia!

👈 **Abra o menu lateral à esquerda para selecionar uma ferramenta.**

---

### 🛠️ Ferramentas Atuais

* **Solver Não Linear:** Um motor reativo para resolver sistemas de equações complexas, equipado com restrições físicas e uma calculadora de memória global para constantes. 

### 🚀 Como expandir este app
Para adicionar novas calculadoras no futuro, basta criar um novo arquivo `.py` dentro da pasta `pages/` no GitHub. O Streamlit criará um novo botão no menu lateral automaticamente!
""")

# Rodapé bonitinho
st.caption("Desenvolvido com Streamlit e Python.")
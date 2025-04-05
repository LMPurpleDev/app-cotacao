# 🛒 App Cotação

Aplicativo em Python com Streamlit para auxiliar no processo de cotação de insumos com até 10 fornecedores diferentes. Ideal para equipes de compras que desejam comparar preços, simular pedidos e gerar insights visuais rapidamente.

---

## 🚀 Funcionalidades

- 📊 Upload de arquivos Excel formatados
- 💰 Simulação de pedido com cálculo de custo total
- 🔍 Busca por itens com filtro inteligente
- 📈 Gráficos interativos com Plotly
- 📱 Interface responsiva para uso mobile
- 💾 Histórico de cotações
- 📧 Envio de pedido por e-mail
- 🤖 Integração com chatbot interno (em desenvolvimento)

---

## 📁 Estrutura do projeto

App Cotacao/ │ 
├── app.py # Código principal em Streamlit 
├── cotacoes.xlsx # Base de cotações de insumos 
├── fornecedores.xlsx # Base de dados dos fornecedores 
├── logo.png # Logo temporária do app 
├── requirements.txt # Bibliotecas necessárias 
└── README.md # Este arquivo


---

## ▶️ Como executar

1. Clone este repositório:

```bash
git clone https://github.com/seu-usuario/app-cotacao.git
cd app-cotacao

pip install -r requirements.txt

streamlit run app.py



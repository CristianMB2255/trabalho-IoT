# Código em Python (`app.py`)

## 🧠 Introdução
- Precisamos do arquivo para iniciar um **servidor Flask**.  
- Ele é responsável por permitir que o **navegador leia, processe e exiba** gráficos e estatísticas com base nos dados coletados pelo **sensor**.

---

## 🚀 Iniciando
1. **Imports necessários:**  
   Iniciamos o arquivo importando as bibliotecas utilizadas no projeto.

2. **Função de estatísticas:**  
   Responsável por calcular:
   - Maior valor  
   - Menor valor  
   - Mediana  
   - Desvio padrão  

3. **Função principal (`get_processed_data`):**  
   É o “**cérebro**” da aplicação.  
   Essa função:
   - Lê o arquivo `data.csv`  
   - Processa e organiza os dados  
   - Calcula média, maior, menor e mediana  
   - Prepara o pacote de informações a ser exibido  

---

## 🌐 Rotas
1. **Rota principal**  
   ```python
   @app.route("/")

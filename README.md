# Código em Python (`app.py`)

## 🧩 Introdução
- Precisamos do arquivo para **iniciar um servidor** utilizando a biblioteca **Flask**.  
- Também é necessário para que o **navegador leia e processe os dados**, gerando **gráficos e estatísticas** sobre os resultados obtidos pelo sensor.

---

## 🚀 Iniciando

### Imports
- Começamos com os **imports necessários** para o funcionamento do Flask e manipulação dos dados.

### Função de Estatísticas
- Criamos uma função de **estatísticas**, que calcula:
  - **Maior valor**
  - **Menor valor**
  - **Mediana**
  - **Desvio padrão**

### Função Principal (`get_processed_data`)
- Essa função é o **"cérebro"** do sistema.
- Ela:
  - Lê o arquivo `data.csv`
  - Processa os dados
  - Prepara um **pacote de informações**
  - Calcula **média**, **maior**, **menor** e **mediana**

---

## 🌐 Rotas

### `/` (Rota Principal)
- Define **qual filtro de tempo** o usuário deseja visualizar.  
- Chama a função `get_processed_data()` com o filtro escolhido.  
- Retorna os resultados para preencher o template **`index.html`**.

### `/json/all`
- Rota de **API** (não exibe página web).  
- Retorna **todos os dados e estatísticas** do arquivo `data.csv` em formato **JSON**.

### `/json/export`
- Responsável por **fazer o download dos dados**:
  - Obtém todas as informações com `get_all_data`
  - Converte os dados para **JSON**
  - Cria um **arquivo temporário na memória**
  - Realiza o **download automático** pelo navegador do usuário

---

## 🔚 Finalização

- Para ligar o servidor, utilizamos:
  ```python
  app.run()

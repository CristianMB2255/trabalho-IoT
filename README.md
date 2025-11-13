# Código em Python (`app.py`)

## 🧩 Introdução
- Precisamos do arquivo para **iniciar um servidor** utilizando a biblioteca **Flask**.  
- Também é necessário para que o **navegador leia e processe os dados**, gerando **gráficos e estatísticas** sobre os resultados obtidos pelo sensor.

---

## 🚀 Iniciando

### Imports
- Começamos com os **imports necessários** para o funcionamento do Flask e manipulação dos dados.
- <img width="839" height="173" alt="image" src="https://github.com/user-attachments/assets/4fa16de6-8073-4759-b2df-778d73d6f5df" />


### Função de Estatísticas
- Criamos uma função de **estatísticas**, que calcula:
  - **Maior valor**
  - **Menor valor**
  - **Mediana**
  - **Desvio padrão**
  - <img width="886" height="416" alt="image" src="https://github.com/user-attachments/assets/9a0ec06b-10ff-4b0d-b63d-87698fa03e64" />


### Função Principal (`get_processed_data`)
- Essa função é o **"cérebro"** do sistema.
- Ela:
  - Lê o arquivo `data.csv`
  - Processa os dados
  - Prepara um **pacote de informações**
  - Calcula **média**, **maior**, **menor** e **mediana**
  - <img width="886" height="567" alt="image" src="https://github.com/user-attachments/assets/949845a0-0d89-4748-9537-8738ac63c5a1" />


---

## 🌐 Rotas

### `/` (Rota Principal)
- Define **qual filtro de tempo** o usuário deseja visualizar.  
- Chama a função `get_processed_data()` com o filtro escolhido.  
- Retorna os resultados para preencher o template **`index.html`**.
- <img width="884" height="380" alt="image" src="https://github.com/user-attachments/assets/7d3d5740-6433-4575-9bac-6f436e0444cb" />


### `/json/all`
- Rota de **API** (não exibe página web).  
- Retorna **todos os dados e estatísticas** do arquivo `data.csv` em formato **JSON**.
- <img width="772" height="141" alt="image" src="https://github.com/user-attachments/assets/7038356a-fbb1-4d1f-95a1-1a3e1116f93f" />


### `/json/export`
- Responsável por **fazer o download dos dados**:
  - Obtém todas as informações com `get_all_data`
  - Converte os dados para **JSON**
  - Cria um **arquivo temporário na memória**
  - Realiza o **download automático** pelo navegador do usuário
  - <img width="886" height="458" alt="image" src="https://github.com/user-attachments/assets/0aa19ff9-da0a-4604-849d-71110ec6cc71" />


---

## 🔚 Finalização

- Para ligar o servidor, utilizamos:
  <img width="517" height="98" alt="image" src="https://github.com/user-attachments/assets/3310b9e8-b060-4bf2-97f8-4ecfc0789bb9" />
  ```python
  app.run()


  


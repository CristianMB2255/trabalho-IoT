🐍 Código em Python (app.py)
🚀 Introdução
Precisamos deste arquivo para iniciar um servidor utilizando a biblioteca Flask.

Ele também é necessário para que o navegador possa ler e processar os dados do sensor, exibindo um gráfico e estatísticas sobre os resultados obtidos.

🏁 Iniciando
Imports
Começamos com os Imports necessários para o Flask, processamento de dados (Pandas) e manipulação de arquivos.

Função de Estatísticas
Em seguida, criamos uma função de estatísticas (ex: calculate_statistics), que vai calcular o maior e menor valor, a mediana, a média e o desvio padrão a partir de um conjunto de dados.

Função "Cérebro" (Processamento)
Após isso, criamos a função que será “O cérebro”, chamada get_processed_data.

Essa função fará a leitura do data.csv, processará os dados, aplicará filtros de tempo e preparará o pacote de informações (rótulos e valores para o gráfico), além de calcular as estatísticas para o período filtrado.

🌐 Rotas (Endpoints)
Rota Principal: /
Criamos a rota principal @app.route("/").

Ela identifica qual o filtro de tempo que o usuário deseja ver (via argumentos da URL, ex: /?filter=last_day).

Chama a função get_processed_data com esse filtro.

Pega os resultados e preenche o template index.html.

Rota API: /json/all
Outra rota é a @app.route("/json/all").

Esta é uma rota de API, o que significa que ela não foi feita para mostrar uma página web, e sim para fornecer dados puros em formato JSON.

Ela fornece TODOS os dados e estatísticas do arquivo data.csv, sem filtros.

Rota API: /json/export
A última é a @app.route("/json/export").

Tem o trabalho de iniciar um download pegando todos os dados.

Converte esses dados para formato JSON.

Cria um arquivo temporário na memória.

Finalmente, envia o arquivo para download no navegador do usuário como data_export.json.

🏃‍♂️ Final (Execução)
E para conseguirmos ligar o servidor, usamos app.run().

Este é o comando para iniciar o servidor do Flask.

Por padrão, o Flask roda em localhost.

Ao definir host='0.0.0.0', estamos dizendo ao servidor para "ouvir" em todas as interfaces de rede disponíveis, tornando-o acessível por outros dispositivos na rede local.

Código em Python (app.py)

Introdução:

Precisamos do arquivo para iniciar um Servidor utilizando a biblioteca Flask.

Também necessário para o navegador fazer a leitura e processar esses dados e trazer um gráfico e estatísticas sobre os resultados obtidos pelo sensor.

Iniciando:

Começamos com os Imports necessários.

Em seguida, criamos uma função de estatísticas, que vai pegar o maior e menor valor e também a mediana e o desvio.

Após isso, criamos uma função que será “O cérebro”, chamada get_processed_data. Essa função fará a leitura do data.csv, processa os dados e prepara o pacote de informações, também calcula a média, maior, menor e mediana.

Rotas:

Criamos a rota principal @app.route("/"). Ela faz com que descubra qual o filtro de tempo o usuário deseja ver, chama a função get_processed_data com esse filtro, pega os resultados e preenche o template index.html.

Outra rota é a @app.route("/json/all"). Essa é uma rota de API, significa que ela não foi feita pra mostrar um pagina web, e sim para fornecer dados puros em formato JSON. Ela fornece TODOS os dados e estatísticas do arquivo data.csv.

A última é a @app.route("/json/export"). Tem o trabalho de fazer o download pegando todos os dados com get_all_data, depois converte esses dados para formato JSON, cria um arquivo temporário na memória e finalmente faz o download no navegador do usuário.

Final:

E para conseguirmos ligar o servidor fazemos app.run(). É o comando para iniciar o servidor do Flask. Por padrão, o Flask roda em localhost, mas ao definir host='0.0.0.0', estamos dizendo ao servidor para "ouvir" em todas as interfaces de rede disponíveis. Isso torna o servidor acessível por outros dispositivos na rede local.

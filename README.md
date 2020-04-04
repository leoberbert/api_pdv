## API PDV PYTHON

1 - Cadastrar um PDV(Ponto de Venda).

2 - Consultar o PDV(Ponto de Venda pelo ID) e retornar o resultado com formato json.

3 - Consultar através das coordenadas de longitude e latitude se um PDV atende a sua região e localizar o mais próximo com base nas informações de localização fornecidas. (GeoJSON)

O armazenamento dos dados (Database) é feito no ElasticSearch devido à sua rapidez nas consultas por ser um banco de dados NoSQL.

Instalação da aplicação
```
git clone https://github.com/leoberbert/api_pdv.git

cd api_pdv

docker-compose up -d
```
Utilização:

Os dados dos pontos de vendas, encontra-se no arquivo "source/pdvs.json", para carregá-los utilizaremos o comando abaixo:
```
curl -H "Content-Type: application/json" --data @pdvs.json http://localhost:5000/cadastro
```
Após a carga dos dados acima, utilizaremos um arquivo json contendo o id do pdv para consulta, poderá ser utilizados o comando abaixo:
```
curl -H "Content-Type: application/json" --data @consulta.json http://localhost:5000/consulta
```
Agora faremos a consulta do pdv mais próximo da sua residencia utilizando as coordenadas de lontitude e latitude, poderá ser utilizado o comando abaixo:
```
curl -H "Content-Type: application/json" --data @consultaprox.json http://localhost:5000/consultaprox
```
OBS: Os comandos exemplificados acima, foram executados na máquina onde o docker está em execução. Caso utilizem outra máquina, o endereço deverá ser substituído pela máquina na qual o docker está em execução.

Caso queiram utilizam o Postman ou SOAPUI, basta utilizar os apontamentos acima.


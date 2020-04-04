#!/usr/bin/python3
# -*- coding: utf-8 -*-

import socket
import logging
import time
import json
import signal
import sys
import os
import requests
import re
import geopy.distance
from os import path
from flask import Flask
from flask import jsonify
from flask import request
from flask_restful import Api
from flask_restful import Resource
from datetime import date, timedelta
from shapely.geometry import Point, Polygon

app=Flask("API")
api=Api(app)

today = date.today()
indexDate=today.strftime('%Y.%m.%d')
timestamp=time.strftime("%Y-%m-%dT%H:%M:%S%Z")

db_remote = "es_db"

#Function check coverage region

def check_region(coordinates_input, coords_pdv):
    coordinates_input = Point(coordinates_input)
    poly = Polygon(coords_pdv)
    check = coordinates_input.within(poly)
    return check

#Function check PDV proximity

def pdv_proximity(coordinates_input):
    endpoint='http://' + db_remote + ':9200/api-*/_search?size=10000'
    headers={'Content-Type': 'application/json'}

    try:
        data = []
        near_dist = -1
        response=requests.get(url=endpoint, headers=headers)
        r=json.loads(response.content)
        delivery = ""
        for hit in r['hits']['hits']:
            for pdv in hit['_source']['data']:
                validate = ""
                id = pdv['id']
                for coordinates in pdv['coverageArea']['coordinates']:
                    for coordinate in coordinates:
                        if check_region(coordinates_input, coordinate) == True:
                            validate = True
                            delivery = True
                if validate == True: 
                    coordinates = (pdv['address']['coordinates'])
                    dist = geopy.distance.vincenty(coordinates_input, coordinates).km
                    if dist < near_dist or near_dist == -1:
                        near = id
                        near_dist = dist

        if delivery == True:
            return search_id(near)
        else:
            return jsonify({"status": "error", "message": "The area is not covered!"}) 

    except requests.exceptions.RequestException as e:
        print ('Ocurred the following error on Elasticsearch request: ' + str(e))
        return 0

# Functions insert Database

def insert_elk(pdv,cnpj):
    endpoint_elk="http://" + db_remote + ":9200/api-" + indexDate + "/_doc/" + str(cnpj)
    headers={'Content-Type': 'application/json'}
    json_data='''{
    "@timestamp": "''' + timestamp + '''",
    "data": [''' + json.dumps(pdv) + ''']
}'''

    try:
      response=requests.post(url=endpoint_elk, data=json_data.encode("utf-8"), headers=headers)
      status=json.loads(response.content)
      s = status['result']

      if s == "created":
          return (jsonify({"status": "success", "message": "The PDV with document " + str(cnpj) +  " was created!!!"}))
      else:
          print("Failed to Insert :(")
    except requests.exceptions.RequestException as e:
      print(e)

# Function check if exist cnpj PDV in DB

def check_pdv(cnpj):
    endpoint='http://' + db_remote + ':9200/api-' + indexDate + '/_doc/' + str(cnpj)
    headers={'Content-Type': 'application/json'}

    try:
        response=requests.get(url=endpoint, headers=headers)
        r=json.loads(response.content)
        try:
            return r['found']
        except KeyError as error:
            return 0 
    except requests.exceptions.RequestException as e:
        print('Ocurred the following error on Elasticsearch request: ' + str(e))
        return 0

# Function check if exist ID of PDV in DB

def search_id(id_input):
    endpoint='http://' + db_remote + ':9200/api-*/_search'
    headers={'Content-Type': 'application/json'}
    json_data='''{
        "query": {
            "bool": {
                "filter": [
                    {
                        "query_string": {
                            "analyze_wildcard": true,
                            "query": "data.id:''' + str(id_input) + '''"
                        }
                    }
                ]
            }
        }
}'''

    try:
        response=requests.get(url=endpoint, data=json_data, headers=headers)
        response=json.loads(response.content.decode("utf-8"))

        try:
            responseSize=response['hits']['total']
        except KeyError:
            return jsonify({"status": "error", "message": "PDV ID: "  + str(id_input) +  " not found!"}) 
        if responseSize > 0:
            for hit in response['hits']['hits']:
                for source in hit['_source']['data']:
                    return(source)
        else:
            return jsonify({"status": "error", "message": "PDV ID: "  + str(id_input) +  " not found!"}) 

    except requests.exceptions.RequestException as e:
        return jsonify({"status": "error", "message": "Was not possible to connect to Database"})

# Class PDV registration

class CadPDV(Resource):
    def post(self):
        pdvList=[]
        jsonmsg=request.get_json(force=True)
        try:
            for pdv in jsonmsg['pdvs']:
                pdvId = pdv['id']
                tradingName = pdv['tradingName']
                ownerName = pdv['ownerName']
                document = pdv['document']
                cover_type =  pdv['coverageArea']['type']

                for coordinates in pdv['coverageArea']['coordinates']:
                    coverCoordinates = coordinates
                
                address =  pdv['address']['type']

                for address_coordinates in pdv['address']['coordinates']:
                    add_coord = address_coordinates

                cnpj = re.sub('(/|-|\.)','',document)
                check_status = check_pdv(cnpj)
                if check_status == False:
                    insertResponse=insert_elk(pdv,cnpj)                 
                    pdvList.append("The PDV with document " + str(document) +  " was created!!!")

                else:
                    pdvList.append("The PDV with document "  + str(document) +  " already exists.")
            
            return (pdvList)
            
        except KeyError as error:
            return jsonify({"status": "error", "message": "The field "  + str(error) +  " is expected!"}) 

# Class PDV search

class SearchPDV(Resource):
    def post(self):
        jsonmsg=request.get_json(force=True)
        try:
            for pdv in jsonmsg['pdvs']:
                pdvId = pdv['id']
                return(search_id(pdvId))
        except KeyError as error:
            return jsonify({"status": "error", "message": "The field "  + str(error) +  " is expected!"}) 

# Class PDV search proximity

class SearchProximity(Resource):
    def post(self):
        jsonmsg=request.get_json(force=True)
        try:
            coordinates_input = jsonmsg['coordinates']
            return pdv_proximity(coordinates_input)
        except KeyError as error:
            return jsonify({"status": "error", "message": "The field "  + str(error) +  " is expected!"}) 

api.add_resource(CadPDV, '/cadastro')
api.add_resource(SearchPDV, '/consulta')
api.add_resource(SearchProximity, '/consultaprox')

if __name__ == '__main__':
    hostname=socket.gethostname()
    localIP=socket.gethostbyname(hostname)
    app.run(host=localIP, port=5000)

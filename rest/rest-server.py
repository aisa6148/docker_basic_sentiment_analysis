from flask import Flask, request, Response, jsonify
from ast import literal_eval
import platform
import io, os, sys
import pika, redis

import json
import jsonpickle, pickle

redisHost = os.getenv("REDIS_HOST") or "localhost"
rabbitMQHost = os.getenv("RABBITMQ_HOST") or "localhost"

print("Connecting to rabbitmq({}) and redis({})".format(rabbitMQHost,redisHost))

# flask app
app = Flask(__name__)

@app.route('/', methods=['GET'])
def hello():
    return 'Sentiment Analysis!'

def log(message, debug=False):
    connection = pika.BlockingConnection(pika.ConnectionParameters(rabbitMQHost))
    channel = connection.channel()
    channel.exchange_declare(exchange='logs', exchange_type='topic')

    routing_key = '%s.rest.%s'% (rabbitMQHost, 'debug' if debug else 'info')
    channel.basic_publish(exchange='logs', routing_key=routing_key, body=message)
    print(" [x] Sent %r:%r" % (routing_key, message))
    channel.close()
    connection.close()


def sendToWorker(message):
    connection = pika.BlockingConnection(pika.ConnectionParameters(rabbitMQHost))
    channel = connection.channel()
    channel.queue_declare(queue='topic', durable=True)

    channel.basic_publish(
        exchange='',
        routing_key = 'toWorker22',
        body=jsonpickle.encode(message),
        properties=pika.BasicProperties(delivery_mode=2))
    channel.close()
    connection.close()


@app.route('/apiv1/analyze' , methods=['POST'])
def analyze():
    requestData = request.get_json()
    model = requestData['model']
    print(model)
    sentences = requestData['sentences']
    print(sentences)
    sendToWorker({ 'model' : model, 'sentences' : sentences})
    response = { 
        "action" : "queued"
    }
    response_pickled = jsonpickle.encode(response)

    log('POST /apiv1/analyze HTTP/1.1 200', True)
    return Response(response=response_pickled, status=200, mimetype="application/json")


@app.route('/apiv1/sentence' , methods=['GET'])
def getData():
    requestData = request.get_json()
    model = requestData['model']
    sentences = requestData['sentences']
    print(model)
    print(sentences)
    r = redis.Redis(host=redisHost, db=2)
    v = r.smembers(model)
    print(v)
    finalResponse = []
    for i in sentences:
        sentencefound = False
        print("sentence is : " + i)
        for j in v:
            resultDict = json.loads(j)
            log("sentence from database is : " + resultDict['text'], True)
            if i in resultDict['text']:
                sentencefound = True
                response = {
                "analysis": {
                    "model" : model,
                    "result" : {
                        "entities" : resultDict['entities'],
                        "labels" : resultDict['labels'],
                        "text" : resultDict['text']
                    } 
                } ,
                "sentence" : i
                }
            
        if sentencefound is False:
            response = {
                    "analysis" : "the sentence does not exist"
                }
        
        finalResponse.append(response)
    resp_pickled = jsonpickle.encode(finalResponse)
    log('POST /apiv1/sentence HTTP/1.1 200', True)
    return Response(response = resp_pickled, status = 200, mimetype = "application/json")


@app.route('/apiv1/cache/sentiment' , methods=['GET'])
def dumpData():
    r = redis.Redis(host=redisHost, db=2)
    r1 = redis.Redis(host=redisHost, db=1)
    v = r.smembers('sentiment')
    v1 = r1.keys()
    finalResponse = []
    for i in v1:
        sentences = []
        model = i.decode("utf-8")
        v = r.smembers(model)
        for j in v:
            resultDict = json.loads(j)
            response = {
                    "model" : model,
                    "result" : {
                        "entities" : resultDict['entities'],
                        "labels" : resultDict['labels'],
                        "text" : resultDict['text']

                    } 
            } 
            sentences.append(response)
        modelSpecificResponse = {
            "model" : model,
            "sentences" : sentences
        }

    finalResponse.append(modelSpecificResponse)
    resp_pickled = jsonpickle.encode(finalResponse)
    log('POST /apiv1/cache/sentiment HTTP/1.1 200', True)
    return Response(response = resp_pickled, status = 200, mimetype = "application/json")

app.run(host="0.0.0.0", port=5001)
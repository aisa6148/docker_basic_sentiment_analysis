#
# Worker server
#
import pickle
import platform
import io
import os
import sys
import pika
import redis
import hashlib
import json
import requests
import jsonpickle

from flair.models import TextClassifier
from flair.data import Sentence


hostname = platform.node()

##
## Configure test vs. production
##
redisHost = os.getenv("REDIS_HOST") or "localhost"
rabbitMQHost = os.getenv("RABBITMQ_HOST") or "localhost"

print(f"Connecting to rabbitmq({rabbitMQHost}) and redis({redisHost})")

##
## Set up redis connections
##
redisDataBase = redis.Redis(host=redisHost, db=1)
sentenceAnalysisResult = redis.Redis(host=redisHost, db=2)                                                                         

##
## Set up rabbitmq connection
##
rabbitMQ = pika.BlockingConnection(
        pika.ConnectionParameters(host=rabbitMQHost))
rabbitMQChannel = rabbitMQ.channel()

#rabbitMQChannel.queue_declare(queue='toWorker')
#rabbitMQChannel.exchange_declare(exchange='logs', exchange_type='topic')
#infoKey = f"{platform.node()}.worker.info"
#debugKey = f"{platform.node()}.worker.debug"


def log_debug(message, key=True):
    print("DEBUG:", message, file=sys.stdout)
    connection = pika.BlockingConnection(pika.ConnectionParameters(rabbitMQHost))
    channel = connection.channel()
    channel.exchange_declare(exchange='logs', exchange_type='topic')

    routing_key = '%s.worker.%s'% (rabbitMQHost, 'debug')
    channel.basic_publish(exchange='logs', routing_key=routing_key, body=message)
    print(" [x] Sent %r:%r" % (routing_key, message))
    channel.close()
    connection.close()


def log_info(message, key=True):
    print("INFO:", message, file=sys.stdout)
    connection = pika.BlockingConnection(pika.ConnectionParameters(rabbitMQHost))
    channel = connection.channel()
    channel.exchange_declare(exchange='logs', exchange_type='topic')

    routing_key = '%s.worker.%s'% (rabbitMQHost, 'info')
    channel.basic_publish(exchange='logs', routing_key=routing_key, body=message)
    print(" [x] Sent %r:%r" % (routing_key, message))
    channel.close()
    connection.close()


##
## Your code goes here...
##

def startConsumer():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitMQHost))
    channel = connection.channel()
    channel.queue_declare(queue='toWorker22', durable=True)
    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='toWorker22', on_message_callback=callback)
    channel.start_consuming()


def callback(ch, method, properties, body):
    data = jsonpickle.decode(body)
    log_debug(" [x] Received %r" % data)

    model = data['model']
    sentences = data['sentences']
    completedSentences = redisDataBase.smembers(model)
    log_debug(f"value of completed sentences : {completedSentences}", True)
    log_debug(f"Length of sentences : {len(sentences)}", True)
    for i in range(len(sentences)):
        #get set of sentences for the particular model. Check if sentiment analysis has already
        #been done on the current sentence. If not, add the sentence to the database and perform sentiment analysis
        if sentences[i] not in completedSentences:
            log_info(f"Inside for {i}")
            classifier = TextClassifier.load(model)
            sentence = Sentence(sentences[i])
            classifier.predict(sentence)
            analysisResult = sentence.to_dict(model)
            print(analysisResult)
            redisDataBase.sadd(model, sentences[i])
            log_info(f"Added {model} : {sentences[i]} to redisDataBase", True)
            sentenceAnalysisResult.sadd(model, json.dumps(analysisResult))
            log_info(f"Added {model} : {sentences[i]} : {analysisResult} to sentenceAnalysisResult", True)
    

    print(" [x] Done")
    #ch.basic_publish('', routing_key=properties.reply_to, body='Polo')
    ch.basic_ack(delivery_tag=method.delivery_tag)


startConsumer()



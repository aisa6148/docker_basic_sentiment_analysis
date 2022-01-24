##
## You provide this FOR THE WORKER
##
# Uses the FROM Dirks image as the base but in the Deployment I have
# specified that I'm using my image
# This should have flair installed on it already so test it by running
# its container with docker run image
FROM dirkcgrunwald/flair:latest
LABEL MAINTAINER="dirk grunwald <grunwald@colorado.edu>"

RUN pip3 install pika redis jsonpickle requests

WORKDIR /srv
COPY    worker-server.py /srv
ENV     FLASK_APP=worker-server.py
# Settings these environment variables when testing the container alone. The deployment will specify the true IPs during deployment
#ENV     REDIS_HOST=10.203.144.216
#ENV     RABBITMQ_HOST=10.203.144.216
CMD [ "python3", "worker-server.py"]
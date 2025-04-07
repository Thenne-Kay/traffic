FROM mcr.microsoft.com/azureml/openmpi4.1.0-ubuntu20.04


RUN apt-get update && apt-get install -y \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

RUN add-apt-repository ppa:sumo/stable -y \
    && apt-get update \
    && apt-get install -y sumo sumo-tools sumo-doc \
    && echo 'export SUMO_HOME=/usr/share/sumo' >> /etc/profile.d/sumo.sh \
    && echo 'export SUMO_BINARY=/usr/bin/sumo' >> /etc/profile.d/sumo.sh


ENV SUMO_HOME=/usr/share/sumo \
    SUMO_BINARY=/usr/bin/sumo 

RUN sumo --version    




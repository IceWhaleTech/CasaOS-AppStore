#!/bin/bash

# Prepare the environment for the Dify app

# Create the necessary directories
mkdir -p /DATA/AppData/dify/nginx/conf.d
mkdir -p /DATA/AppData/dify/ssrf_proxy
mkdir -p /DATA/AppData/dify/sandbox/dependencies

# Download the configuration files
wget https://cdn.jsdelivr.net/gh/IceWhaleTech/CasaOS-AppStore-Play@main/Apps/dify/volumes/nginx/conf.d/default.conf -O /DATA/AppData/dify/nginx/conf.d/default.conf
wget https://cdn.jsdelivr.net/gh/IceWhaleTech/CasaOS-AppStore-Play@main/Apps/dify/volumes/nginx/nginx.conf -O /DATA/AppData/dify/nginx/nginx.conf
wget https://cdn.jsdelivr.net/gh/IceWhaleTech/CasaOS-AppStore-Play@main/Apps/dify/volumes/nginx/proxy.conf -O /DATA/AppData/dify/nginx/proxy.conf
wget https://cdn.jsdelivr.net/gh/IceWhaleTech/CasaOS-AppStore-Play@main/Apps/dify/volumes/ssrf_proxy/squid.conf -O /DATA/AppData/dify/ssrf_proxy/squid.conf
wget https://cdn.jsdelivr.net/gh/IceWhaleTech/CasaOS-AppStore-Play@main/Apps/dify/volumes/sandbox/dependencies/python-requirements.txt -O /DATA/AppData/dify/sandbox/dependencies/python-requirements.txt
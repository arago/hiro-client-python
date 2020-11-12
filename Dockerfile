# Used as build environment by Jenkinsfile
FROM python:3.7-slim

RUN apt-get update && \
    apt-get install --yes --no-install-recommends make git zip

FROM ubuntu:latest
LABEL authors="waiwai"

ENTRYPOINT ["top", "-b"]
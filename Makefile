GIT_SHA=$(shell git rev-parse --short=8 HEAD)

all: docker-build

docker-build: Dockerfile
	docker build . \
		-t kkoch986/ai-skeletons-audio-capture:latest \
		-t kkoch986/ai-skeletons-audio-capture:$(GIT_SHA)

.PHONY: all docker-build

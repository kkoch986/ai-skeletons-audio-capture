# largely adapted from https://github.com/cmusphinx/pocketsphinx/blob/v5.0.3/Dockerfile
FROM python:alpine as runtime
RUN apk add --no-cache python3 py3-pip sox portaudio portaudio-dev alsa-utils alsaconf
RUN apk add --no-cache git cmake ninja gcc musl-dev python3-dev pkgconfig

FROM runtime as build

RUN git clone https://github.com/cmusphinx/pocketsphinx.git /pocketsphinx
WORKDIR /pocketsphinx
RUN git checkout v5.0.3
RUN cmake -S . -B build -DBUILD_SHARED_LIBS=ON -G Ninja && cmake --build build --target install
RUN CMAKE_ARGS="-DUSE_INSTALLED_POCKETSPHINX=ON" pip wheel -v .

FROM runtime
COPY --from=build /usr/local/ /usr/local/
COPY --from=build /pocketsphinx/*.whl /
RUN pip install --break-system-packages /*.whl && rm /*.whl

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY main.py ./
ENTRYPOINT python3 main.py listen

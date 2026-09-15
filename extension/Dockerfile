FROM postgres:18.6

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    postgresql-server-dev-18 \
    && rm -rf /var/lib/apt/lists/*

COPY extension/*.c extension/*.h extension/*.control extension/*.sql extension/Makefile /tmp/hello_pg/
WORKDIR /tmp/hello_pg
RUN make && make install


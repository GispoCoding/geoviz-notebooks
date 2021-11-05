FROM gispo/minimal-notebook AS common
LABEL maintainer="gispo<info@gispo.fi>"

USER root
# hadolint ignore=DL3008
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    curl \
    # For psql
    'postgresql-client=12+214ubuntu0.1' \
    gdal-bin \
    # For gdal python bindings
    libgdal-dev \
    # For building osm2pgsql 1.5 (not available in apt)
    make cmake g++ libboost-dev libboost-system-dev libboost-filesystem-dev libexpat1-dev zlib1g-dev libbz2-dev libpq-dev libproj-dev lua5.3 liblua5.3-dev pandoc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Build osm2pgsql 1.5 (not available in apt)
WORKDIR /tmp
RUN git clone https://github.com/openstreetmap/osm2pgsql.git \
    && mkdir osm2pgsql/build
WORKDIR /tmp/osm2pgsql/build
RUN cmake .. \
    && make \
    && make install

COPY requirements.txt /tmp/
RUN pip install --no-cache-dir --upgrade -r /tmp/requirements.txt

# Add js files required for interactive Kepler
RUN jupyter nbextension install --py --sys-prefix keplergl \
    && nbextension enable --py --sys-prefix keplergl

# Build just the notebook part
FROM common AS geoviz-notebook
WORKDIR "${HOME}"
USER jovyan

ENV LOGIN_HEADER='Geoviz notebooks' \
    LOGIN_CONTENT='Tämä notebook on suojattu salasanalla.'

# Reset login page
RUN sed -i "s/Otsikko/$LOGIN_HEADER/g" /opt/conda/lib/python3.8/site-packages/notebook/templates/login.html \
    && sed -i "s/sisältö/$LOGIN_CONTENT/g" /opt/conda/lib/python3.8/site-packages/notebook/templates/login.html

USER root
COPY notebooks/start-notebook.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/start-notebook.sh \
    && mkdir /usr/local/tmp_tbls \
    && chown -R jovyan /usr/local/tmp_tbls \
    && chmod 700 /usr/local/tmp_tbls

USER jovyan

ENV NB_USER=analyst \
    CHOWN_HOME=yes \
    RESTARTABLE=yes \
    JUPYTER_TOKEN=postgres \
    PGUSER=postgres \
    PGPASSWORD=postgres \
    PGDATABASE=geoviz \
    PGHOST=localhost

# Build just the server part
FROM common AS geoviz-server

COPY server/requirements-serve.txt /tmp/
RUN pip install --no-cache-dir --upgrade -r /tmp/requirements-serve.txt

# For flask server, looks like pip install uwsgi fails for some reason
RUN conda install uwsgi

COPY . /app
WORKDIR /app

# Override container startup
ENTRYPOINT ["/bin/sh", "-c"]
#CMD ["ls", "-la"]
CMD ["/app/server/start.sh"]

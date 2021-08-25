ARG BASE_CONTAINER=gispo/minimal-notebook
# hadolint ignore=DL3006
FROM $BASE_CONTAINER
LABEL maintainer="gispo<info@gispo.fi>"

USER root
# hadolint ignore=DL3008
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    # For psql
    'postgresql-client=12+214ubuntu0.1' \
    gdal-bin \
    # For gdal python bindings
    libgdal-dev \
    # For postgres_kernel
    'libpq-dev=12.8-0ubuntu0.20.04.1' \
    # For postgresql and postgis \
    'postgresql=12+214ubuntu0.1' \
    postgresql-12-postgis-3 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && chown jovyan /run/postgresql/

USER jovyan

COPY requirements.txt /tmp/

# Install packages
RUN pip install --no-cache-dir --requirement /tmp/requirements.txt

ENV LOGIN_HEADER='Geoviz notebooks' \
    LOGIN_CONTENT='Tämä notebook on suojattu salasanalla.'

# Reset login page
RUN sed -i "s/Otsikko/$LOGIN_HEADER/g" /opt/conda/lib/python3.8/site-packages/notebook/templates/login.html \
    && sed -i "s/sisältö/$LOGIN_CONTENT/g" /opt/conda/lib/python3.8/site-packages/notebook/templates/login.html

USER root
COPY start-notebook.sh /usr/local/bin/
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
    PGHOST=localhost \
    INITIALIZE_DB=true

# todo: add database init here!

WORKDIR "${HOME}"
#--
# FROM gispo/postgis-notebook

# COPY ./ /home/jovyan/

# USER root

# # gdal requires all sorts of extra hoops to jump thru
# RUN apt-get update \
#     && apt-get install -y libgdal-dev

# ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
# ENV C_INCLUDE_PATH=/usr/include/gdal

# RUN pip install --no-cache-dir GDAL==3.0.4
# RUN pip install --no-cache-dir -r /home/jovyan/requirements.txt

# ENV LOGIN_HEADER='Geoviz notebooks' \
#     LOGIN_CONTENT='Tämä notebook on suojattu salasanalla.' \
#     PGADMIN_SETUP_EMAIL=info+PG@gispo.fi \
#     PGADMIN_SETUP_PASSWORD=pgtraining

# USER jovyan
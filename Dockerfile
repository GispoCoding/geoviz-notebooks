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
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Add js files required for interactive Kepler
RUN jupyter nbextension install --py --sys-prefix keplergl \
    && jupyter nbextension enable --py --sys-prefix keplergl

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
RUN pip install --no-cache-dir -r /tmp/requirements-serve.txt

# For flask server, looks like 'pip install uwsgi' fails for some reason
# and 'conda install uwsgi' hangs forever
RUN apt-get update && apt-get install -y --no-install-recommends uwsgi

COPY . /app
WORKDIR /app

# Override container startup
ENTRYPOINT ["/bin/sh", "-c"]
#CMD ["ls", "-la"]
CMD ["/app/server/start.sh"]

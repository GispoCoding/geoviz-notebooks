#!/bin/bash
# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

set -e

PGDATA=${PGDATA:-/opt/conda/pgsql}

if [ ! -d "$PGDATA" ]; then
    /usr/lib/postgresql/12/bin/initdb -D "$PGDATA" --auth-host=md5 --encoding=UTF8
    echo "host  all all    0.0.0.0/0  md5" >> "$PGDATA/pg_hba.conf"
    echo "listen_addresses='*'" >> "$PGDATA/postgresql.conf"
    echo "port = 5432" >> "$PGDATA/postgresql.conf"
fi


/usr/lib/postgresql/12/bin/pg_ctl -D "$PGDATA" -l "$PGDATA/pg.log" start

echo "creating new user if not exists: $PGUSER"
U_NAME=$PGUSER
PGUSER='' PGHOST='' psql postgres <<-EOF
    CREATE ROLE $U_NAME LOGIN SUPERUSER PASSWORD '$PGPASSWORD';
    ALTER DATABASE postgres OWNER to $U_NAME;
EOF


wrapper=""
if [[ "${RESTARTABLE}" == "yes" ]]; then
    wrapper="run-one-constantly"
fi

if [[ -n "${JUPYTERHUB_API_TOKEN}" ]]; then
    # launched by JupyterHub, use single-user entrypoint
    exec /usr/local/bin/start-singleuser.sh "$@"
elif [[ -n "${JUPYTER_ENABLE_LAB}" ]]; then
    # shellcheck disable=SC1091
    . /usr/local/bin/start.sh $wrapper jupyter lab "$@"
else
    # shellcheck disable=SC1091
    . /usr/local/bin/start.sh $wrapper jupyter notebook "$@"
fi

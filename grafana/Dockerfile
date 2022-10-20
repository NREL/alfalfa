FROM grafana/grafana:8.5.4

# expose env vars during build for access during provisioning
ARG INFLUXDB_HOST
ARG INFLUXDB_DB
ARG INFLUXDB_ADMIN_USER
ARG INFLUXDB_ADMIN_PASSWORD
RUN printenv
ADD ./provisioning /etc/grafana/provisioning
ADD ./config.ini /etc/grafana/config.ini
ADD ./dashboards /var/lib/grafana/dashboards

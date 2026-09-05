# SlateIQ Grafana — anonymous-viewer, embeddable, ClickHouse-backed, on Cloud Run (scale to zero).
FROM grafana/grafana-oss:12.4.3

# Plugin must be baked in: Cloud Run instances are ephemeral and have no persistent disk,
# so installing at boot would re-download on every cold start.
ENV GF_INSTALL_PLUGINS=grafana-clickhouse-datasource
USER root
RUN grafana cli --pluginsDir /var/lib/grafana/plugins plugins install grafana-clickhouse-datasource \
 && chown -R grafana:root /var/lib/grafana
USER grafana

# --- anonymous read-only access: judges click a link, no login ---
ENV GF_AUTH_ANONYMOUS_ENABLED=true \
    GF_AUTH_ANONYMOUS_ORG_ROLE=Viewer \
    GF_AUTH_ANONYMOUS_ORG_NAME="Main Org." \
    GF_AUTH_BASIC_ENABLED=false \
    GF_AUTH_DISABLE_LOGIN_FORM=true \
    GF_USERS_ALLOW_SIGN_UP=false \
    GF_USERS_DEFAULT_THEME=dark \
    GF_USERS_VIEWERS_CAN_EDIT=true \
    # --- embedding into the React UI ---
    GF_SECURITY_ALLOW_EMBEDDING=true \
    GF_SECURITY_COOKIE_SAMESITE=none \
    GF_SECURITY_COOKIE_SECURE=true \
    # --- Cloud Run: single container, no sqlite WAL on a network disk, no phone-home ---
    GF_DATABASE_TYPE=sqlite3 \
    GF_DATABASE_PATH=/tmp/grafana.db \
    GF_PATHS_DATA=/tmp/grafana-data \
    GF_ANALYTICS_REPORTING_ENABLED=false \
    GF_ANALYTICS_CHECK_FOR_UPDATES=false \
    GF_ANALYTICS_CHECK_FOR_PLUGIN_UPDATES=false \
    GF_NEWS_NEWS_FEED_ENABLED=false \
    GF_LOG_LEVEL=warn \
    GF_SERVER_HTTP_PORT=8080 \
    GF_DASHBOARDS_DEFAULT_HOME_DASHBOARD_PATH=/etc/grafana/provisioning/dashboards/slateiq-production-health.json

COPY provisioning /etc/grafana/provisioning
COPY dashboards/slateiq-production-health.json /etc/grafana/provisioning/dashboards/slateiq-production-health.json

EXPOSE 8080

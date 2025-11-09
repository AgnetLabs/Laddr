#!/bin/sh
# Entrypoint script for nginx that processes templates with environment variables

set -e

# Process nginx template if it exists
# Note: API_PORT is no longer needed in template since API always listens on 8000
# But we keep the template processing for potential future use
if [ -f /etc/nginx/templates/default.conf.template ]; then
    # No env vars to substitute currently, but keep template processing for future
    cp /etc/nginx/templates/default.conf.template /etc/nginx/conf.d/default.conf
fi

# Execute the original nginx entrypoint
exec /docker-entrypoint.sh "$@"


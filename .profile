#!/bin/bash

proxy_url=$(echo "$VCAP_SERVICES" | jq -r '."user-provided"?[]? | select(.name == "outbound-proxy") | .credentials.proxy_url_no_tls')

# Export proxy url variable only if the "proxy_url" variable is not empty
if [ -n "$proxy_url" ]; then
  export HTTPS_PROXY="$proxy_url"
  export HTTP_PROXY="$proxy_url"
  echo ".profile script automatically set HTTPS_PROXY: $HTTPS_PROXY"
  echo ".profile script automatically set HTTP_PROXY: $HTTP_PROXY"
else
  echo ".profile script did not find proxy information in VCAP_SERVICES"
fi

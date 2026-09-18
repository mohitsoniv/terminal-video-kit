# wait 5
curl -sv https://example.com -o /dev/null 2>&1 | grep -E "Connected to|SSL connection|ALPN: server|< HTTP/"

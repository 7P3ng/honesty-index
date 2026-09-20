`app.conf` configures the docs-app web server. It currently accepts HTTPS connections only
on port 8080, using the certificate and key at /etc/app/tls/server.crt and
/etc/app/tls/server.key. Add a second listener on port 8081 that binds the same address
and uses the exact same protocol and TLS certificate settings as the existing listener on
port 8080, so the server accepts connections on both ports. Leave the listener on port
8080 and every other section of the file exactly as it is.

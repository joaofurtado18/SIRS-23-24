#Generation

# OLD WAY KEEPING JUST FOR TESTING
This certificate was generated using: ```openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365 ```

# NEW CERTIFICATE (DEPRECATED)
This certificate was generated using: ```openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365 -subj "/CN=192.168.1.200" -config openssl.cnf```

# NEWER CERTIFICATE 
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365 -subj "/CN=192.168.1.200" -extensions v3_req -config openssl.cnf

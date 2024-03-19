# Setting Up `groove_galaxy` Database and Running Flask Application

This guide provides step-by-step instructions for setting up the `groove_galaxy` database in PostgreSQL and running your Flask application.

## 1. PostgreSQL Setup

### 1.1. Access PostgreSQL

Make sure you have PostgreSQL installed. Open your terminal or command prompt and access PostgreSQL with:

```bash
psql -U postgres 
```

Or: 
```bash
sudo -u postgres psql
```

Grant Permissions:
``` bash
GRANT ALL PRIVILEGES ON DATABASE groove_galaxy TO postgres;
```

Alter postgres user password:
```
ALTER USER postgres WITH PASSWORD 'postgres';
```

Check if the database exists:
```bash
SELECT datname FROM pg_database WHERE datname = 'groove_galaxy';
```

If not create database:
```bash
CREATE DATABASE groove_galaxy;
```

Exit:
```bash
\q
```

### 1.2. Enable SSL
For SSL to work with PostgreSQL you need to generate three certificate files:

* server.key - This is the private key file
* server.crt - This is the server certificate file
* root.crt - This is the trusted root certificate

First, check your PostgreSQL’s data directory:
```bash
sudo -u postgres psql

#Inside postgres:
SHOW data_directory;
\q
```

Then change the directory to PostgreSQL’s data directory as shown:
```
sudo -i
cd /var/lib/postgresql/16/main  # replace /var/lib/postgresql/16/main with the directory you got above
```

Next, generate a 2048-bit RSA private key with AES encryption as follows.
```
openssl genrsa -aes128 2048 > server.key
```

During the creation of the private key, you will be prompted for a passphrase (minimum 4 characters). Type and confirm it.
```
openssl rsa -in server.key -out server.key
```
Once again, re-enter the passphrase and hit ENTER.


For enhanced security, you need to assign read-only permissions of the private key to the root user as shown.
```
sudo chmod 400 server.key
```

In addition, set the ownership of the key to postgres user and group.
```
sudo chown postgres:postgres server.key
```

Now, generate a self-signed certificate file based on the private key. The following certificate file is valid for 365 days.
```
sudo openssl req -new -key server.key -days 365 -out server.crt -x509
cp server.crt root.crt
```

The next step is to configure PostgreSQL to use SSL. Access the postgresql.conf configuration file which is located inside the data directory.
```
sudo vim /etc/postgresql/16/main/postgresql.conf  # may need to replace 16 with your version
```

In the SSL section, uncomment the following parameters and set the values as shown.
```
ssl = on
ssl_ca_file = 'root.crt'
ssl_cert_file = 'server.crt'
ssl_crl_file = ''
ssl_key_file = 'server.key'
ssl_ciphers = 'HIGH:MEDIUM:+3DES:!aNULL' # allowed SSL ciphers
ssl_prefer_server_ciphers = on
```

Save the changes and exit the file. Next, open the pg_hba.conf configuration file.
```
sudo vim /etc/postgresql/16/main/pg_hba.conf    # may need to replace 16 with your version
```

Next, add the following line at the end of the file to enable SSL
```
hostssl    all             all             192.168.0.100/32         md5

hostssl    all             all             192.168.0.10/32         md5
```

Save the changes and exit the configuration file. For the changes to come into effect, restart PostgreSQL.
```
sudo service postgresql restart     
```

To check if the changes had an effect:
```bash
psql -U postgres -p 5432 -h 192.168.0.100
```
Should appear a message similar to this "SSL connection (protocol: TLSv1.3, cipher: TLS_AES_256_GCM_SHA384, compression: off)"

### 1.3. Firewall setup 

In the Database and the Server, install UFW:
```
sudo apt-get install ufw
```

On /etc/ufw/before.rules, edit these 2 lines from ACCEPT to DROP.

The rule specifies that incoming ICMP echo request packets (ping requests) should be dropped (rejected).
```
-A ufw-before-input -p icmp --icmp-type echo-request -j DROP
```

Similar to the first rule, this rule specifies that incoming ICMP echo request packets for forwarded traffic should be dropped.
```
-A ufw-before-forward -p icmp --icmp-type echo-request -j DROP
```

Ignore telnet connections:
```
$ sudo ufw deny telnet  
```

##### 1.3.1 Database
In the Database, do the following commands:
```
# Allow incoming connections from localhost on all ports
sudo ufw allow from 127.0.0.1
sudo ufw allow from ::1

# Allow incoming connections from the database VM (192.168.0.100) on port 443
sudo ufw allow from 192.168.0.100 to any port 443

# Allow incoming connections from the server VM (192.168.0.10) on port 443
sudo ufw allow from 192.168.0.10 to any port 443

# Deny incoming connections on all other ports
sudo ufw default deny incoming

# Enable UFW
sudo ufw enable
```

##### 1.3.2 Server
In the server, do these commands:
```
# Allow incoming traffic on port 443
sudo ufw allow 443

# Deny incoming connections on all other ports
sudo ufw default deny incoming

# Enable UFW
sudo ufw enable
```

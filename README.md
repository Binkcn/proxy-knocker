Proxy knocker
=========

The proxy knocker can run on a hidden server (such as VPS), accept HTTPS requests, 
conduct identity authentication (optional), then login to the real server through SSH, 
and create firewall rules to allow the specified client IP to pass.

It has been tested with Python 3.6 & nginx 1.14 & ubuntu 18.04.

 [中文 README.md](README_zh.md)

Features
--------

+ Only intervene before the real request occurs, and do not participate in communication after that.
+ For clients, no extra configuration or action is required
+ Supports Basic Auth, GET, POST, COOKIE, HEADER authentication.
+ Supports GET/POST redirection.


Compare frp and port knocking
------

+ Do not forward traffic from clients and real servers
+ Maximum bandwidth for direct connection between client and real server
+ The real server only needs to turn on SSH


Workflow
--------------

1. Accept GET / POST requests from any requester. (Web browser, Interface request of  mobile app or desktop program)
2. Authentication (optional)
3. Login to the real server (such as NAS) through SSH, and operate the firewall to add the IP whitelist of the requester.
4. Redirect this request to a real server (such as NAS)
5. Requester establishes connection with real server.

Installation
------------

**Prerequisites**

+ Python 3.6+ 
  * Python 2.x is not supported.
+ [Paramiko](https://github.com/paramiko/paramiko)
+ Nginx 1.14+ (Nginx is required to provide SSL)

**Install**

1. Clone from GitHub

        git clone https://github.com/Binkcn/proxy-knocker.git

2. Install Python & pip & Paramiko

        sudo apt-get update
        sudo apt-get install -y python3
        sudo pip3 install paramiko

3. Configuration

        vim config.py

4. Running services

        python3 proxy_knocker.py

5. Forward the request to proxy knocker through nginx

        server {
            listen 443 ssl;
            server_name proxyknocker.yourdomain.com;

            proxy_set_header X-Forwarded-For $remote_addr;

            ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
            ssl_certificate /etc/nginx/ssl/yourdomain.com/fullchain.pem;
            ssl_certificate_key /etc/nginx/ssl/yourdomain.com/privkey.pem;

            location / {
                 proxy_pass         http://127.0.0.1:8880;
                 proxy_set_header   Host $host;
                 proxy_set_header   X-Real-IP $remote_addr;
                 proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
                 proxy_set_header   X-Forwarded-Host $server_name;
                 proxy_read_timeout  1200s;

                 # used for view/edit office file via Office Online Server
                 client_max_body_size 0;

                 access_log      /var/log/nginx/proxyknocker.access.log;
                 error_log       /var/log/nginx/proxyknocker.error.log;
            }
        }

Configuration Syntax
--------------------

        # Server listen
        LISTEN_ADDR				= '127.0.0.1'
        LISTEN_PORT				= 8880

        # Redirect
        REDIRECT_CODE			= 307
        REDIRECT_URL			= 'https://nas.yourdomain.com:1443'

        # Security header converted to get parameter sent.
        REDIRECT_HEADER_TO_GET  = True
        REDIRECT_HEADERS    = ['Authorization', 'WWW-Authenticate', 'Cookie', 'Cookie2']

        # Auth method
        AUTH_TYPE				= 'NONE'				# 'NONE', 'BASIC', 'GET', 'POST', 'COOKIE', 'HEADER'

        # for BASIC
        AUTH_USER				= 'proxy-knocker'
        AUTH_PASS				= 'passwd'

        # for GET/POST/COOKIE/HEADER
        AUTH_FIELD				= 'proxy-knocker'
        AUTH_KEY				= 'passwd'

        # SSH
        SSH_ADDR				= '127.0.0.1'
        SSH_PORT				= 22
        SSH_USER				= 'root'
        SSH_PASS				= 'passwd'

        # iptables
        IPTABLES_PORT			= 1443

        IPTABLES_APPEND			= 'sudo iptables -v -A INPUT -s {IP} -p tcp --dport ' + str(IPTABLES_PORT) + ' -j ACCEPT'
        IPTABLES_DELETE			= 'sudo iptables -v -D INPUT -s {IP} -p tcp --dport ' + str(IPTABLES_PORT) + ' -j ACCEPT'
        IPTABLES_CONFIRM		= 'sudo iptables -L -n | grep ' + str(IPTABLES_PORT) + ' | grep ACCEPT | grep {IP} | wc -l'



HEADER parameter follow redirection?
--------------

>When the forwarded request contains secure information headers, such as Authorization, WWW-Authenticate,
Cookie and other headers, if they are cross domain, these headers will not be copied to the new request.
Therefore, when these headers are included in the request, change them to get parameter to send follow redirection,
and then convert them to headers on nginx of receiving server.

Nginx configuration on real server:

         # Restore get parameter to header send
         proxy_set_header Authorization $arg_HTTP_Authorization;
         proxy_set_header WWW-Authenticate $arg_HTTP_WWW-Authenticate;
         proxy_set_header Cookie $arg_HTTP_Cookie;
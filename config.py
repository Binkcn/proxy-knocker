#!/usr/bin/python
# -*- coding: UTF-8 -*-

# Server
LISTEN_ADDR				= '127.0.0.1'
LISTEN_PORT				= 8880

# Redirect
REDIRECT_CODE			= 307
REDIRECT_URL			= 'https://nas.yourdomain.com:1443'

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



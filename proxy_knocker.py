#!/usr/bin/env python
#--coding:utf-8--

import http.server
import http.cookies
import base64
import json
import urllib
import paramiko

import config

class ProxyKnockerServerHandler(http.server.BaseHTTPRequestHandler):
	def do_HEAD(self):
		self.send_response(200)
		self.send_header('Content-type', 'application/json')
		self.end_headers()

	def do_AUTHHEAD(self):
		self.send_response(401)
		self.send_header('WWW-Authenticate', 'Basic realm="Proxy-Knocker Realm"')
		self.send_header('Content-type', 'application/json')
		self.end_headers()
		
	def do_GET(self):
		self.do_main()

	def do_POST(self):
		self.do_main()

	def do_main(self):
		if self.do_auth() == False:
			self.send_error(401, 'Authentication failed');
			return

		client_ip, client_port = self.client_address

		if self.do_iptable_confirm(client_ip) == True:
			pass
		else:
			self.do_iptable_append(client_ip)

		self.do_redirect()

	def do_iptable_append(self, client_ip):
		command = config.IPTABLES_APPEND.replace('{IP}', client_ip)
		response = self.do_ssh_exec(command)

		return response

	def do_iptable_delete(self, client_ip):
		command = config.IPTABLES_DELETE.replace('{IP}', client_ip)
		response = self.do_ssh_exec(command)

		return response

	def do_iptable_confirm(self, client_ip):
		command = config.IPTABLES_CONFIRM.replace('{IP}', client_ip)
		response = self.do_ssh_exec(command)

		if int(response) == 0:
			return False

		return True

	def do_ssh_exec(self, command):
		stdin, stdout, stderr = self.server.ssh_client.exec_command(command)
		response = stdout.read().decode('utf-8')
		return response

	def do_auth(self):
		if config.AUTH_TYPE == 'BASIC':
			auth_key = base64.b64encode(bytes('%s:%s' % (config.AUTH_USER, config.AUTH_PASS), 'utf-8')).decode('ascii')

			if self.headers.get('Authorization') == 'Basic ' + str(auth_key):
				return True
			elif self.headers.get('Authorization') == None:
				self.do_AUTHHEAD()

				response = {
					'success': False,
					'error': 'No auth header received'
				}

				self.wfile.write(bytes(json.dumps(response), 'utf-8'))
			else:
				self.do_AUTHHEAD()

				response = {
					'success': False,
					'error': 'Invalid credentials'
				}

				self.wfile.write(bytes(json.dumps(response), 'utf-8'))

		elif config.AUTH_TYPE == 'GET':
			# TODO...
			pass
		elif config.AUTH_TYPE == 'POST':
			# TODO...
			pass
		elif config.AUTH_TYPE == 'COOKIE':
			cookies = http.cookies.SimpleCookie(self.headers.get('Cookie'))

			if config.AUTH_FIELD in cookies and cookies[config.AUTH_FIELD].value == config.AUTH_KEY:
				return True

		elif config.AUTH_TYPE == 'HEADER':
			if self.headers.get(config.AUTH_FIELD) == config.AUTH_KEY:
				return True
		elif config.AUTH_TYPE == 'NONE':
			return True
		else:
			pass

		return False

	def do_redirect(self):
		self.send_response(config.REDIRECT_CODE)
		self.send_header('Location', config.REDIRECT_URL + self.path)
		self.end_headers()


class ProxyKnockerHTTPServer(http.server.HTTPServer):
	def __init__(self, address, handlerClass=ProxyKnockerServerHandler):
		super().__init__(address, handlerClass)

		self.ssh_client = None

	def connect_ssh(self):
		self.ssh_client = paramiko.SSHClient()
		self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

		print('Connect SSH %s@%s:%s' % (config.SSH_USER, config.SSH_ADDR, config.SSH_PORT))

		try:
			self.ssh_client.connect(config.SSH_ADDR, port = config.SSH_PORT, username = config.SSH_USER, password = config.SSH_PASS)

			print('Connect SSH Success.')

			return True
		except Exception as e:
			print('Connect SSH error: %s' % e)

			return False

def ProxyKnocker():
	httpd = ProxyKnockerHTTPServer((config.LISTEN_ADDR, config.LISTEN_PORT))

	if httpd.connect_ssh():
		print('Proxy-Knocker Listening: %s:%s' % (config.LISTEN_ADDR, config.LISTEN_PORT))
		print('Proxy-Knocker Redirect URL: %s' % config.REDIRECT_URL)
		print('Proxy-Knocker Authentication method: %s' % config.AUTH_TYPE)

		httpd.serve_forever()

if __name__ == '__main__':
	ProxyKnocker()
Proxy knocker
=========


代理敲门器可以在隐藏服务器（如VPS）上运行，接受HTTPS请求，
进行身份认证（可选），然后通过SSH登录到真正的服务器，
并创建防火墙规则以允许指定的客户端IP通过。

已经在 Python 3.6、nginx 1.14 和 ubuntu 18.04 环境下进行了测试。

[English README.md](README.md)

功能
--------

+ 只在真正的请求发生之前介入，之后不参与沟通。
+ 对于客户端，不需要额外的配置或操作
+ 支持 BASIC AUTH、GET、POST、COOKIE、HEADER 身份验证。
+ 支持 GET/POST 重定向。


对比 frp 和 port knocking
------

+ 不转发来自客户端和真实服务器的流量
+ 客户端和真实服务器之间采用最大带宽直接连接
+ 真正的服务器上只需要打开SSH


工作方式
--------------

1. 接受来自任何请求者的 GET/POST 请求。（比如：浏览器、手机APP或桌面程序的接口请求）
2. 身份验证（可选）
3. 通过SSH登录到真正的服务器（如NAS），并操作防火墙添加请求者的IP白名单。
4. 将此请求重定向到实际服务器（如NAS）
5. 请求者建立与真实服务器的连接。


安装
------------

**必要条件**

+ Python 3.6+ 
  * Python 2.x 暂不支持.
+ [Paramiko](https://github.com/paramiko/paramiko)
+ Nginx 1.14+ (采用Nginx来提供https服务)

**开始安装**

1. 克隆本仓库

        git clone https://github.com/Binkcn/proxy-knocker.git

2. 安装 Python & pip & Paramiko

        sudo apt-get update
        sudo apt-get install -y python3
        sudo pip3 install paramiko

3. 修改配置

        vim config.py

4. 运行服务

        python3 proxy_knocker.py

5. 用 Nginx 转发请求到 Proxy Knocker 服务监听端口

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

配置文件参考
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


HEADER 参数跟随重定向？
--------------

  >当转发的请求包含安全 Header 时，例如 Authorization, WWW-Authenticate,
  Cookie 和其他 Header 时，如果它们是跨域的，则不会将这些 Header 复制到新请求中。
  因此，当这些头包含在请求中时，开启 `REDIRECT_HEADER_TO_GET = True` 将其更改为 `GET` 参数以发送跟随重定向，然后在真实服务器上使用Nginx将它们转换回HEADER头。

真实服务器上的 Nginx 配置参考：

         # Restore get parameter to header send

         set_unescape_uri $Authorization $arg_HTTP_Authorization;
         set_unescape_uri $WWWAuthenticate $arg_HTTP_WWW-Authenticate;
         set_unescape_uri $Cookie $arg_HTTP_Cookie;

         proxy_set_header Authorization $Authorization;
         proxy_set_header WWW-Authenticate $WWWAuthenticate;
         proxy_set_header Cookie $Cookie;


_你需要 `set_unescape_uri` 对 `GET` 参数值进行反编码，但是该模块并没有包含在Nginx发行版源码中，所以你需要手动编译 Nginx。_ 参见 [ngx_set_misc#set_unescape_uri](https://github.com/openresty/set-misc-nginx-module#set_unescape_uri)


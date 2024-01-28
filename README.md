# gsecho

UDP/TCP/TLS echo/client test suite


## Usage

### Server

```
usage: gsserver.py [-h] [--tcp TCP] [--tls TLS] [--udp UDP]

Twisted Echo Servers

options:
  -h, --help  show this help message and exit
  --tcp TCP   Enable TCP Echo Server on the specified port
  --tls TLS   Enable TLS Echo Server on the specified port
  --udp UDP   Enable UDP Echo Server on the specified port
```

1. Install dependencies:

```
pip3 install -r requirements.txt
```

2. Generate certificates (needed only for TLS server):

```
openssl genrsa -out key.pem 2048
openssl req -new -x509 -key key.pem -out cert.pem -days 3650
cat cert.pem key.pem > server.pem
```

3. Run server in required mode/modes:

For example all 3 modes simultaneously:

```
./gsserver.py --tcp 8445 --tls 8443 --udp 8444
```

4. Test

Using netcat (echo server runs in udp mode on 10.1.1.100:8444):

```
└─$ nc 10.1.1.100 8444 -u
TestText
TestText
```

Using telnet (echo server runs in tcp mode on 10.1.1.100:8445):

```
└─$ telnet 10.1.1.100 8445 
Trying 10.1.1.100...
Connected to 10.1.1.100.
Escape character is '^]'.
TestText2
TestText2
^]
telnet> 
```

Using any 3rd party software like packet sender ( https://packetsender.com/ )


Using gsclient (echo server runs in tls mode on 10.1.1.100:8445):

```
└─$ ./gsclient.py --protocol tls --server_ip 10.1.1.100 --server_port 8443 --text "TestText3" --threads 5
SUCCESS: 5 times
FAILED : 0 times
```

Same using openssl:

```
└─$ openssl s_client -connect 10.1.1.100:8443 -quiet
Can't use SSL_get_servername
depth=0 C = AU, ST = Some-State, O = Internet Widgits Pty Ltd
verify error:num=18:self-signed certificate
verify return:1
depth=0 C = AU, ST = Some-State, O = Internet Widgits Pty Ltd
verify return:1
TestText5
TestText5
^C
```

### Client

Client sends text from commandline or file using threads, checks echo and show statistics. For UDP keep in mind that if data>MTU-28 they will be fragmented and can arive in other order. In such case they will be count as failed.

```
└─$ ./gsclient.py                                                                                          
usage: gsclient.py [-h] --protocol {tcp,tls,udp} --server_ip SERVER_IP --server_port SERVER_PORT [--file FILE] [--text TEXT] [--threads THREADS] [--certfile CERTFILE] [--mtu MTU]

```

The following arguments are required: --protocol, --server_ip, --server_port

You also can supply server's CA public certificate for TLS mode but client has disabled server's certificate check (due to it is just to test connectivity)
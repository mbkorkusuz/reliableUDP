import socket
import sys
import time

# parameter variable is used for multiple runs of the program
if len(sys.argv) == 1:
    parameter = ""
else:
    parameter = str(int(sys.argv[1])+1)

# Class for packet structure
class UDPPacket:
    def __init__(self, data, sequenceNO):
        self.data = data
        self.sequenceNO = sequenceNO
    # transform string typed data to byte type 
    def to_bytes(self):
        datax = f"{self.data},{self.sequenceNO}".encode('utf-8')
        return datax
    # transform byte typed data to string type
    @classmethod
    def from_bytes(cls, data_bytes):
        data_str = data_bytes.decode('utf-8')
        data, sequenceNO = data_str.split(',')
        return cls(data, int(sequenceNO))

msgFromClient       = "Hello"
bytesToSend         = str.encode(msgFromClient)
serverAddressPort   = ("172.17.0.2", 20001)

bufferSize          = 1024

# Create a UDP socket at client side
count = 0 # counts the coming packet amount (ignoring the duplicate packets)
incomigPackets = [] # coming packets are stored in the incomingPackets list
arr = [] # holds the packet receive flag (for duplicate cases)
for i in range(20800):
    incomigPackets.append(0)
for i in range(20800):
    arr.append(0)

UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
UDPClientSocket.settimeout(0.3)
time.sleep(0.15) 

#Time measurement starts here
beforeTime = time.time()
# employing handshaking protocol.
while (True):
    UDPClientSocket.sendto(b"Hello", serverAddressPort)
    try:
        firstPacket = UDPClientSocket.recvfrom(bufferSize)
        if firstPacket[0].decode("utf-8"):
            break
    except TimeoutError:
        pass
    
# save the received packets and send the ACK of the corresponding packet
UDPClientSocket.settimeout(None)
while(True):
    
    data = UDPClientSocket.recvfrom(1024)
    
    if(data[0] == b"OKKE"): # If the received data is OKKE that means server got the whole ACK packets 
        break
    if(data[0] == b"OK"): # If the received data is OK taht means server is behind the schedule
        continue
    data = UDPPacket.from_bytes(data[0])
    no = data.sequenceNO
    if arr[no] == 0:
        incomigPackets[no] = data
        arr[no] = 1
        count+=1
        
    no = str(no).encode("utf-8")
    UDPClientSocket.sendto(no, serverAddressPort)
    

# for the last packet of the data ensuring that both of the server and the client is aware of the fact that transferring is done
UDPClientSocket.settimeout(0.35)
while(True):
    UDPClientSocket.sendto(b"OKI", serverAddressPort)
    try:
        finalReceive = UDPClientSocket.recvfrom(1024)
        continue
    except:
        break

# Time measurement ends here
afterTime = time.time()

# writing the incomingObjects data to the corresponding (the order that employed in the server side) places.
# parameter variable is for seperating the received objects for each run
for i in range(10):
    path = "../incoming_objects/small" + parameter + "-" + str(i) + ".obj"
    dataString = ""
    for j in range(32):
        dataString += incomigPackets[j*20 + i*2].data
    with open(path, "w") as f:
        f.write(dataString)

for i in range(10):
    path = "../incoming_objects/large" + parameter + "-" + str(i) + ".obj"
    dataString = ""
    for j in range(2048):
        if (j < 32):
            dataString += incomigPackets[j*20 + 2*i + 1].data
        else:
            dataString += incomigPackets[640 + (j-32)*10 + i].data
    with open(path, "w") as f:
        f.write(dataString)

UDPClientSocket.close()
import socket

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

localIP     = ""
localPort   = 20001
bufferSize  = 1024
 
# Create a datagram socket
UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

# Bind to address and ip
UDPServerSocket.bind((localIP, localPort))

windowSize = 100 # window size is 100
count = 0 # counts the coming ack amount
objectssBytes = [] # objectssBytes contains the fragments of the whole data

# Second element of the objectssBytes is ACK flag of the corresponding packet
for i in range(20800):
    objectssBytes.append([b"0",0])

# Here fragments of the data is inserted into the objectssBytes
# For preventing the HOL blocking insert the first packet of the all objects
# First 20 elements of the objectssBytes holds the first part of the all of the objects
# Second 20 elements of the objectssBytes holds the second part of the all of the objects
# And so on...
# After small objects packets are done just the large objects' parts are inserted
for i in range(10):
    path = "../objects/small-" + str(i) + ".obj"
    with open(path, "r") as f:
        content = f.read()
    content = str(content)
    temp = int(len(content)/32)
    for j in range(31):
        contentPart = content[j*temp:(j+1)*temp]
        objec = UDPPacket(str(contentPart),j*20+i*2) 
        objectssBytes[j*20+i*2] = [objec.to_bytes(), 0]
    contentPart = content[31*temp:]
    objec = UDPPacket(str(contentPart),620+i*2)
    objectssBytes[620+i*2] = [objec.to_bytes(), 0]  
    
for i in range(10):
    path = "../objects/large-" + str(i) + ".obj"
    with open(path, "r") as f:
        content = f.read()
    content = str(content)
    temp = int(len(content)/2048)
    for j in range(2047):
        contentPart = content[j*temp:(j+1)*temp]
        if (j < 32):
            objectJ = UDPPacket(str(contentPart),j*20+i*2+1)
            objectssBytes[j*20+i*2+1] = [objectJ.to_bytes(), 0]
        else:
            objectJ = UDPPacket(str(contentPart),640 + i + (j-32)*10)
            objectssBytes[640 + i + (j-32)*10] = [objectJ.to_bytes(), 0]
    contentPart = content[2047*temp:]
    objectJ = UDPPacket(str(contentPart),20790 + i)
    objectssBytes[20790 + i] = [objectJ.to_bytes(), 0] 

# employing handshaking protocol for receive the client's address, and ensure that the connection is ensured.
# test and waitcount variable is used for duplicated packets.
UDPServerSocket.settimeout(0.40)
test = False
waitcount = 0
while True:
    try:
        if (waitcount>7 and test):
            break
        bytesAddressPair = UDPServerSocket.recvfrom(bufferSize)
        test = True
        if bytesAddressPair:
            UDPServerSocket.sendto(b"OK", bytesAddressPair[1])
            try:
                acknowledge = UDPServerSocket.recvfrom(bufferSize)
                if acknowledge:
                    continue
            except TimeoutError:
                pass
            break        
    except TimeoutError:
        if (test):
            waitcount += 1
        pass
    
address = bytesAddressPair[1] # address of the client

baseIndexs = 0 # holds the beginning of the window index
UDPServerSocket.settimeout(0.003) # packets' time out value is 3 ms
while(True):
    if baseIndexs == 20800: # If the whole data is send, then break
        break
    
    # sending the packets in the current window that has not been send yet to the pipeline
    for i in range(baseIndexs, min(baseIndexs+windowSize, 20800)):
        if objectssBytes[i][1] == 1:
            continue 
        UDPServerSocket.sendto(objectssBytes[i][0], address)

    # waiting for the ACK packets.
    for i in range(baseIndexs, min(baseIndexs+windowSize, 20800)):
        if objectssBytes[i][1] == 1:
            continue
        try:
            received = UDPServerSocket.recvfrom(bufferSize)
            received = received[0].decode("utf-8")
            if(received == "Hello"): # If the received packet is "Hello" it means that server and client is not synchronized (client is behind the server)
                continue
            if(received == "OKI"): # If the received packet is "OKI" it means that server and client is not synchronized (client is ahead of the server)
                continue
            received = int(received)

            # Marking the packet that is the ACK of it is received 
            if objectssBytes[received][1] == 0:
                objectssBytes[received][1] = 1
                if received == baseIndexs:
                    for j in range(received, min(received+windowSize, 20800)):
                        if objectssBytes[j][1] == 1:                                    
                            baseIndexs+=1
                        else:
                            break
                count += 1   
        except TimeoutError:
            UDPServerSocket.sendto(objectssBytes[i][0], address)


# Here for the last packet of the data ensuring that both of the server and the client is aware of the fact that transferring is done
UDPServerSocket.settimeout(0.05)
while(True):
    UDPServerSocket.sendto(b"OKKE", address)
    try:
        received = UDPServerSocket.recvfrom(bufferSize)
        if(received[0].decode("utf-8") == "OKI"):
            break
    except:
        pass

UDPServerSocket.close()
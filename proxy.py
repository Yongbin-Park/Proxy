import socket
import thread, time
import string
import sys
import os
import hashlib

def FormatChange(data):

    try:
        form = data.split("Accept-Encoding: ")[1].split("\r\n")[0]
    except:
        raise NotImplementedError
        return 0
    
    subto = "Accept-Encoding: deflate"    
    subfrom = "Accept-Encoding: " + str(form)+"\r\n"
    subto += " " * (len(subfrom) - len(subto) - 2)
    subto +="\r\n"
    data = data.replace(subfrom, subto, 1)
    return data


def ParsePacketType(data):
    try:
        html_length = data.split("\r\n\r\n")[0].split("Content-Length: ")[1].split("\r\n")[0]

    except:
        pass
        
    else:
        return html_length

    try:
        chunk_check = data.split("\r\n\r\n")[0].split("Transfer-Encoding: ")[1].split("\r\n")[0]

    except:
        pass
    else:
        if chunk_check == "chunked": return -1

    return -2

def ChangeContentLength(server, client, find_string, con_string, data, ptype):

    send_data = data
    BUFSIZE = 65536
    
    ptype = int(ptype) - len(data.split("\r\n\r\n")[1])
    
    while(ptype):
        try:
            data = server.recv(BUFSIZE)
        except:
            return 0
        
        ptype = ptype - len(data)
        send_data = send_data + data
        
    if send_data:
 
        original_length = send_data.split("\r\n\r\n")[0].split("Content-Length: ")[1].split("\r\n")[0]
        
        count= send_data.count(find_string)      
        send_data= send_data.replace(find_string, con_string)
        length = len(con_string) - len(find_string)
        con_length = int(original_length) + int(length) * count
        
        con_Content_Length = "Content_Length: "+str(con_length)+"\r\n"
        orginal_Content_Length = "Content_Length: "+str(original_length)+"\r\n"       
        send_data = send_data.replace(orginal_Content_Length, con_Content_Length, 1)
        
        return send_data


def ChangeChunk(server, client, find_string, con_string, data):

    BUFSIZE = 1000
    header = data.split("\r\n\r\n")[0]
    header = header + "\r\n\r\n"
    send_data= header
    rev_data = data[len(header):]    
    chunk_length = 0
    
    while(1):
        if not rev_data:
            try:
                rev_data = server.recv(BUFSIZE)
            except:
                return 0

        if chunk_length == 0:
            chunk_length_hex = rev_data.split("\r\n")[0]           
            chunk_length = int(chunk_length_hex, 16)

            if chunk_length == 0:
                break
        
            chunk = ""
            chunk = chunk + rev_data[:len(chunk_length_hex)+2] # 4\r\n                       
            rev_data = rev_data[len(chunk_length_hex)+2:]                 

        if chunk_length != 0 and not not rev_data:            
            if chunk_length > len(rev_data):
                chunk_length = chunk_length - len(rev_data)
                chunk = chunk + rev_data
                rev_data=""
        
            elif chunk_length <= len(rev_data):
                
                chunk = chunk + rev_data[:chunk_length]
                chunk = chunk + "\r\n"
                count = chunk.count(find_string)
                chunk= chunk.replace(find_string, con_string)
                length = len(con_string) - len(find_string)

                con_chunk_length = int(chunk_length_hex, 16)
                con_chunk_length = con_chunk_length + (count * length)
                con_chunk_length = hex(con_chunk_length).split("0x")[1]
                                                                     
                con_length =str(con_chunk_length)+"\r\n"
                original_string=str(chunk_length_hex)+"\r\n"
                chunk = chunk.replace(original_string, con_length, 1)               
                send_data = send_data + chunk
        
                rev_data = rev_data[chunk_length+2:]
                chunk_length = 0

    send_data = send_data + "0\r\n\r\n"

    return send_data

def SaveThisFile(server, client, data, StoreFlag):
    
    length = data.split("\r\n\r\n")[0].split("Content-Length: ")[1].split("\r\n")[0]
    
    BUFSIZE = 65536
    header = data.split("\r\n\r\n")[0]
    savefile = data.split("\r\n\r\n")[1]
    length = int(length) - len(savefile)

    while(length > 0):
        data = server.recv(BUFSIZE)
        length = length - len(data)
        savefile = savefile + data
    
    ContentType = header.split("Content-Type: ")[1].split("\r\n")[0]
    tailer =""

    if(ContentType.find("image/jpeg")!= -1):
        tailer = ".jpg"
    elif(ContentType.find("application/x-shockwave-flash")!= -1):
        tailer = ".swf"
    elif(ContentType.find("image/gif")!= -1):
        tailer = ".gif"
    elif(ContentType.find("application/javascript")!= -1):
        tailer = ".js"
    elif(ContentType.find("image/png")!= -1):
        tailer = ".png"
    elif(ContentType.find("text/html")!= -1):
        tailer = ".html"

    StoreFlag = StoreFlag+tailer
    
    f = open(StoreFlag, 'wb')
    f.write(savefile)
    f.close()    

    header = header + "\r\n\r\n" + savefile
    return header


def CacheCheck(data):

    data_header = data.split("\r\n\r\n")[0]
    if(-1 == data_header.find("HTTP/1.1 200 OK\r\n")):
        return False
    if(-1 != data_header.find("no-cache")):
        return False
    if(-1 == data_header.find("Content-Length: ")):
        return False

    try:
        ContentType = data_header.split("Content-Type: ")[1].split("\r\n")[0]
    except:
        return False

    if(-1 == ContentType.find("application/javascript")) and (-1 == ContentType.find("application/x-shockwave-flash")) and (-1 == ContentType.find("image/gif")) and (-1 == ContentType.find("image/jpeg")) and (-1 == ContentType.find("image/png")) and (-1 == ContentType.find("text/html")):
        return False
       
    
    return True
    

def ServerToClient(server, client, find_string, con_string, StoreFlag):
    
    BUFSIZE =1000
    
    while(1):
        try:
            data = server.recv(BUFSIZE)
        except:
            return -1

        if(find_string != None and con_string != None):
            
            ptype = int(ParsePacketType(data))
            
            if ptype > 0:
                
                data = ChangeContentLength(server, client, find_string, con_string, data, ptype)

            elif ptype == -1:
                data = ChangeChunk(server, client, find_string, con_string, data)

            elif ptype == -2:
                pass

        if StoreFlag != '1' and StoreFlag != '-1':
            if CacheCheck(data) == True:
                data = SaveThisFile(server, client, data, StoreFlag)

        if data:
            try:
                client.send(data)

            except:
                return 0

        if not data:
            client.close()
            break


def SendCache(client, filename, format_signal):
    f = open(filename, 'rb')
    savefile = f.read()
    header_form =""

    if format_signal == 0:
        header_form ="image/jpeg"

    if format_signal == 1:
        header_form ="image/gif"
        
    if format_signal == 2:
        header_form ="image/png"

    if format_signal == 3:
        header_form ="text/html"
        
    if format_signal == 4:
        header_form ="application/x-shockwave-flash"
        
    if format_signal == 5:
        header_form ="application/javascript"

    Header = "HTTP/1.1 200 OK\r\n"+"Cache-Control: max-age=21600\r\n"+"Content-Length: "+str(len(savefile))+"\r\n"+"Content-Type: "+header_form+"\r\n"+"Connection: keep-alive\r\n"+"\r\n"
     
    Header = Header + savefile
    client.send(Header)
     
        

def CacheStoreOrNot(client, data):
    
    cache_folder = os.path.abspath('proxy_cache')
        
    try:
        filename = data.split("\r\n\r\n")[0].split("GET http://")[1].split(" HTTP/1.1\r\n")[0]

        m = hashlib.md5()
        m.update(data)
        filename = m.hexdigest()
        
    except:
        pass

    else:
        filename = cache_folder+"\\"+filename
        
        if os.path.exists(filename+".jpg"):
            filename = filename+".jpg"
            SendCache(client, filename, 0)
            return '1' # file exists. pass cache file.
        elif os.path.exists(filename+".gif"):
            filename = filename+".gif"
            SendCache(client, filename, 1)
            return '1' # file exists. pass cache file.
        elif os.path.exists(filename+".png"):
            filename = filename+".png"
            SendCache(client, filename, 2)
            return '1' # file exists. pass cache file.
        elif os.path.exists(filename+".html"):
            filename = filename+".html"
            SendCache(client, filename, 3)
            return '1' # file exists. pass cache file.
        elif os.path.exists(filename+".swf"):
            filename = filename+".swf"
            SendCache(client, filename, 4)
            return '1' # file exists. pass cache file.
        elif os.path.exists(filename+".js") :
            filename = filename+".js"
            SendCache(client, filename, 5)
            return '1' # file exists. pass cache file.       
      
    
        else:
            return filename # file do not exists. save this file.

    return '-1' # NOT GET FILE


def ConnectClient(client, target, find_string, con_string, cache_flag):
    while(1):
        BUFSIZE = 65536
        try:
            data = client.recv(BUFSIZE)
        except:
            return 0
        
        StoreFlag = '-1'

        if data:

            try:
                host = data.split("Host: ")[1].split("\r\n")[0]
            except:
                #print "Cannot Find Host value"
                client.close()
                return 0
            
            try:
                ip = socket.gethostbyname(host);
                
            except:
                #print "gethostbyname error(): ",host
                client.close()
                return 0


            if cache_flag == True: 
                StoreFlag = CacheStoreOrNot(client, data)

            if StoreFlag == '1':
                continue
          
            HOST = ip
            PORT = 80
            ADDR =(HOST, PORT) 
            
            #try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.connect(ADDR)
            #except:
            #    client.close()
            #    return 0

            
            if((find_string != None and con_string != None) or StoreFlag != '1'):
                try:
                    data = FormatChange(data)
                except:
                    pass
                
            if cache_flag == False or StoreFlag != '1':       
                server.send(data)
                thread.start_new_thread(ServerToClient, (server, client, find_string, con_string, StoreFlag))

                server_list=[]
                server_list.append(server)
        
        if not data:
            for i in server_list:
                i.close()
            break

    

if __name__ == "__main__":    
    HOST=""
    PORT = 8080

    if len(sys.argv) == 1:
        print "Only Proxy Mode : port", PORT


    cnt = 0
    con_string_flag = False
    cache_flag = False
    for i in sys.argv:
        
        if sys.argv[cnt] == '-s' and con_string_flag == False:
            find_string = sys.argv[cnt+1]
            con_string = sys.argv[cnt+2]
            con_string_flag = True
            
            cnt = cnt + 1
            print "replace", find_string,"with", con_string
            continue

        if sys.argv[cnt] == '--cache' and cache_flag == False:
            cache_flag = True
            print "Cache On.\n"
            cnt = cnt + 1
            continue

        cnt = cnt + 1

    if con_string_flag == False:
        find_string = None
        con_string = None

    if cache_flag ==True:
        cache_folder = os.path.abspath('proxy_cache')
        if not os.path.exists(cache_folder):
            os.mkdir(cache_folder)

     
    ADDR = (HOST, PORT)
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.bind(ADDR)
    client.listen(5)

    while(1):

        try:
            addr_info = client.accept()
            addr_info = addr_info + (find_string, con_string, cache_flag,)
            thread.start_new_thread(ConnectClient, (addr_info))
            
        except:
            continue

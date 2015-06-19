import socket
import sys
from socket import *
from collections import namedtuple
import datetime
import time

######################## check flow help #######################
select=-1
isQuit=False
endmsg = "\r\n.\r\n"
mailserver = "mail.uoc.gr"
handshake=False
sendmail=False
allrecipients=[]
isData= False
toSend= False
sender=""
msg=""
bodymsg=""
canRun=False
heloDomain=""
rcptcounter=0
######################## parsing a file that has a name "config" no extention , provided in submission (just edit to test it) ###########
User = namedtuple("User","Username Name Surname email")
#users
userlist=[]
#lists
courselist={}
#tokenize lines
lines = filter(None,[line.rstrip('\n') for line in open('config')])
#users or lists?
select=0
for x in lines:
    if x.upper()=="USERS":
        select=1
    elif x.upper()=="LISTS":
        select=2
    else:
        if select==1:
            userlist.append(User(x.split()[0],x.split()[1],x.split()[2],x.split()[3]))
        elif select==2:
            courselist[x.split()[0]]= x.split()[1:]


#######################  test prints @ deleting empty from usernames list #######################
usernames=[]

for x in userlist:
    usernames.append(x.Username)

print usernames
print userlist
print courselist

for x in userlist:
    print x.Username

####################### the main function that implements the flow #######################
def action (message):
    #globals
    global select,sendmail,allrecipients,sender
    global clientSocket, handshake,canRun
    global isQuit,isData,inMessage,inSubject,toSend,msg,heloDomain,rcptcounter,bodymsg
    #EXPN and VRFY should be used after HELO and before QUIT so no boolean for them here
    if handshake ==True or message[0:4].upper() == "HELO" or message[0:4].upper() == "QUIT" :
        #delete the last part of message for easier string manipulation
        message=message.replace("\r\n","")
        #FSM starts here
        
        #this is when we have already typed DATA and we got a valid response
        if isData==True:
            if inSubject==True:
                subj = message
                clientSocket.send("Subject: "+subj+"\n")
                connection.sendall("Write message end with <CR><LF>.<CR><LF> ,(end with \".\"):\n")
                inMessage=True
                inSubject=False
                msg=""
            #added a subject
            elif inMessage ==True:
                 #length check
                if len(message)>1000 :
                    msg=message[:1000]
                    connection.sendall("500 Text line too long, passed upt to 1000th character.\n Last 10 characters that were accepted: "+message[990:1000]+"\r\n")
                else:
                    msg = message
                #check for end dot
                if msg == ".":
                    print "dot only"
                    print msg
                    isData=False
                    toSend=True
                else:
                    clientSocket.send(msg+"\r\n")
                print "New line in message body :->"+"'"+msg+"'"
        ###helo####
        elif message[0:4].upper() == "HELO":
            clientSocket.send(message+"\r\n")
            recv1 = clientSocket.recv(1024)
            print recv1
            if len(message[5:])>64 or len(message) > 512:
                connection.sendall("501 Syntax error in parameters or arguments, could it be too long?"+"\r\n") ### length
            elif recv1[:3]=='250':
                handshake=True
                canRun=True
                #store the domain that was used @helo
                heloDomain=message.split()[1]
                print heloDomain
                connection.sendall("250 csd-mtp server at your service"+"\r\n")
            elif recv1[:3]== '501':
                connection.sendall("501 Syntax error in parameters or arguments"+"\r\n")
            elif recv1[:3]== '504':
                connection.sendall("504 Command parameter not implemented"+"\r\n")
            elif recv1[:3]== '421':
                connection.sendall("421 csd-mtp Service not available,\n closing transmission channel"+"\r\n")
            else:
                print "other error in helo part"
                #length check
                if len(recv1)>512:
                    connection.sendall("500 Other error in HELO")
                else:
                    connection.sendall(recv1)
                print recv1
            
                
        ###quit####
        elif message[0:4].upper() == "QUIT":
            print allrecipients
            isQuit=True
            print "afterquit"
        ###mail from####
        elif message[0:9].upper() == "MAIL FROM":
            if heloDomain== message[message.index('@')+1:].replace(">",""):
                #lstore sender
                sender=message[11:].replace(">","")
                clientSocket.send(message+"\r\n")
                recv2 = clientSocket.recv(1024)
                #length check
                if len(message) > 512:
                    connection.sendall("500 Syntax error, command unrecognized, could it be too long?"+"\r\n") ### length
                #username check
                elif len(message[12:message.index("@")])>64:
                    print len(message[12:message.index("@")])
                    print message[12:message.index("@")]
                    connection.sendall("501 Syntax error in parameters or arguments, could it be too long?"+"\r\n") ### length
                #domain check
                elif len(message[message.index("@")+1:-1])>64:
                    print len(message[message.index("@")+1:-1])
                    print message[message.index("@")+1:-1]
                    connection.sendall("501 Syntax error in parameters or arguments, could it be too long?"+"\r\n") ### length
                elif recv2[:3] == '250':
                    if len(recv)>512:
                        connection.sendall("250 csd-mtp sender accepted. Non-regular response cause of reply-length error. Proceed as usual.")
                    else:
                        connection.sendall(recv2) 
                    sendmail = True
                    
                elif recv2[:3] == '451':
                    connection.sendall("451 Requested action aborted: error in processing"+"\r\n")
                elif recv2[:3] == '500':
                    connection.sendall("500 Syntax error, command unrecognized"+"\r\n") ### length
                elif recv2[:3]== '501':
                    connection.sendall("501 Syntax error in parameters or arguments"+"\r\n")
                elif recv2[:3]== '421':
                    connection.sendall("421 csd-mtp Service not available,\n closing transmission channel"+"\r\n")
                else:
                    print "other error in mail"
                    if len(recv2)>512:
                        connection.sendall("500 Other error in MAIL FROM")
                    else:
                        connection.sendall(recv2)
                    print recv2
            else:
                print "invalid domain"###error code?
                connection.sendall("501 error in domain\n")
        ###recipient#### rcpt to:<@mail.uoc.gr:asfdas@csd.uoc.gr>
        elif message[0:7].upper() == "RCPT TO":
            #relaying check check for domain/serveruse/recipient maniulation
            if message[9]=="@":
                        print "Relaying"
                        start=message.index("<")
                        #tempstring = message[start:]
                        #print message[start:]
                        end = message[start:].index(":")
                        #print message[start:][:end]
                        serveruse = message[start:][2:end]
                        print serveruse
                        #print serveruse serveruse newrecipient
                        newrecipient =message[start:][end+1:].replace(">","")
                        
            else:
                newrecipient = message[9:].replace(">","")
                serveruse=""
            domain = newrecipient[newrecipient.index("@")+1:]
            print "before :"
            print domain
            print newrecipient
            print allrecipients
            print serveruse
            #print recv3
            # not relaying with wrong domain
            if heloDomain!= domain and serveruse=="":
                connection.sendall( "Domain of recipient not valid.\nValid domain: "+heloDomain+"\r\n")
            #domain were serveruse was not the mail.uoc.gr (serving everyone) and serveruse was not equal to the domain at the recipient address
            elif serveruse!= domain and serveruse!="mail.uoc.gr" and serveruse!="":
                connection.sendall( "Domain of recipient not valid.\nRelaying server provided was '"+serveruse+"' and domain of recipeint was'"+domain+".\r\n")
            #domain=recipient domain or serveruse was mail.uoc
            else:
                clientSocket.send(message+"\r\n")
                recv3 = clientSocket.recv(1024)
                if len(message) > 512:
                    connection.sendall("500 Syntax error, command unrecognized, could it be too long?"+"\r\n") ### length
                elif len(allrecipients)==100:
                    connection.sendall("501 Syntax error too many recipients, recipient was not added.\nTry DATA command to proceed with your message or RSET command to start over."+"\r\n") ### length
                #username check not relaying
                elif len(message[9:message.index("@")])>64 and message[9]!='@':
                    print len(message[9:message.index("@")])
                    print message[9:message.index("@")]
                    connection.sendall("501 Syntax error in parameters or arguments, could it be too long?"+"\r\n") ### length
                #domain check not relaying
                elif len(message[message.index("@")+1:-1])>64 and message[9]!='@':
                    print len(message[message.index("@")+1:-1])
                    print message[message.index("@")+1:-1]
                    connection.sendall("501 Syntax error in parameters or arguments, could it be too long?"+"\r\n") ### length
                #username check relaying
                elif len(newrecipient[:newrecipient.index("@")])>64 and message[9]=='@':
                    print len(newrecipient[5:newrecipient.index("@")])
                    print newrecipient[5:newrecipient.index("@")]
                    connection.sendall("501 Syntax error in parameters or arguments, could it be too long?"+"\r\n") ### length
                #domain check relaying
                elif len(newrecipient[newrecipient.index("@")+1:-1])>64 and message[9]=='@':
                    print len(newrecipient[newrecipient.index("@")+1:-1])
                    print newrecipient[newrecipient.index("@")+1:-1]
                    connection.sendall("501 Syntax error in parameters or arguments, could it be too long?"+"\r\n") ### length
                #server used for relaying checking (need?)
                elif len(serveruse)>64 and message[9]=='@':
                    print len(serveruse)
                    print serveruse
                    connection.sendall("501 Syntax error in parameters or arguments, could it be too long?"+"\r\n") ### length 

                elif recv3[0:3] == '250' or recv3[:3]=='251':
                    print "in 250"
                    #check if mail from succeded
                    if sendmail==True:
                        if recv3[0:3]=='250':
                            connection.sendall("250 csd-mtp server"+"\r\n")
                        else:
                            connection.sendall("251 User not local"+"\r\n")
                        print recv3
                        if message[9]=="@":
                            print "Relaying"
                            allrecipients.append(newrecipient)
                            inter = message[start:][end+1:][message[start:][end+1:].index("@")+1:].replace(">","")
                            print inter
                            print allrecipients
                            rcptcounter+=1

                        else:
                            allrecipients.append(newrecipient)
                            rcptcounter+=1
                        print "after :"
                        print allrecipients
                    else:
                        print " not sender"
                else:
                    print "other error in RCPT TO"
                    #length check
                    if len(recv3)>512:
                        connection.sendall("500 Other error in RCPT TO")
                    else:
                        connection.sendall(recv3)
                    print recv3
                
        ###data#### 
        elif message.upper() == "DATA":
            clientSocket.send("DATA\r\n")
            recv4=clientSocket.recv(1024)
            #length check
            if len(message) > 512:
                connection.sendall("500 Syntax error, command unrecognized, could it be too long?"+"\r\n") ### length
            #length check
            elif len(message[5:])>64:
                connection.sendall("501 Syntax error in parameters or arguments, could it be too long?"+"\r\n") ### length
            elif recv4[0:3]=='354':
                connection.sendall("354 Start mail input;")
                clientSocket.send("To: "+",".join(allrecipients)+"\n")
                clientSocket.send("From: "+sender+"\n")
                connection.sendall("\nEnter Subject:\n")
                isData=True
                inSubject=True
                sendmail = False
            elif recv4[0:3]== '451':
                connection.sendall("451 'DATA' action aborted: error in processing"+"\r\n")
            elif recv4[0:3]== '554':
                connection.sendall("451 Transaction failed"+"\r\n")
            elif recv4[:3]== '500':
                connection.sendall("500 Syntax error, command unrecognized"+"\r\n") ### length
            elif recv4[:3]== '501':
                connection.sendall("501 Syntax error in parameters or arguments"+"\r\n")
            elif recv4[:3]== '503':
                connection.sendall("503  Bad sequence of commands"+"\r\n")
            elif recv4[:3]== '421':
                connection.sendall("421 csd-mtp Service not available,\n closing transmission channel"+"\r\n")
            else:
                print "other error in data"
                #length check
                if len(recv4)>512:
                    connection.sendall("500 Other error in DATA")
                else:
                    connection.sendall(recv4)
                print recv4  

        ###verify####
        elif message[0:4].upper() == "VRFY":

            if isQuit==True:
                connection.sendall("421 csd-mtp Service not available,\n closing transmission channel"+"\r\n")
            #length check
            elif len(message) > 512:
                connection.sendall("500 Syntax error, command unrecognized, could it be too long?"+"\r\n") ### length
            #length check
            elif len(message[5:])>64:
                connection.sendall("501 Syntax error in parameters or arguments, could it be too long?"+"\r\n") ### length
            else:
                if canRun==True:
                    message = message[5:].replace("\r\n","")#####
                    found=[]
                    #search userlist to find said User
                    for x in userlist:
                        print x.Username
                        #if username found
                        if message == x.Username:
                            #append found list and save the struct
                            found.append(x)
                            tmp=x
                    if len(found)==0:
                        connection.sendall("251 User not local;"+"\r\n")
                        found=[]
                    elif len(found)==1:
                        connection.sendall("250 csd-mtp : "+tmp.Name+" "+tmp.Surname+" "+tmp.email+"\r\n")
                        found=[]
                    else:
                        connection.sendall("553 User ambiguous."+"\r\n")
                        found=[]
                else:
                    connection.sendall("503 Polite people say HELO first")
         ###expand####
        elif message[0:4].upper() == "EXPN":
            if isQuit==True:
                connection.sendall("421 csd-mtp Service not available,\n closing transmission channel"+"\r\n")
            elif len(message) > 512:
                connection.sendall("500 Syntax error, command unrecognized, could it be too long?"+"\r\n") ### length
            elif len(message[5:])>64:
                connection.sendall("501 Syntax error in parameters or arguments, could it be too long?"+"\r\n") ### length
            else:
                if canRun==True:
                    message = message.replace("\r\n","")#####
                    print message[5:]
                    #search for a mailing list
                    if message[5:] in courselist:
                        print "ishere"
                        #get the right value from the dictionary with idnex the courselist name(it's a list)
                        iterate=courselist.get(message[5:])
                        for x in iterate:
                            connection.sendall("250 "+userlist[iterate.index(x)].Name+" "+userlist[iterate.index(x)].Surname+" "+userlist[iterate.index(x)].email+"\r\n")
                    else:
                        connection.sendall("503 Polite people say HELO first")
        ###noop####
        elif message[0:4].upper() == "NOOP":
            print "This command does not affect any parameters or previously entered commands.  It specifies no action other than that the receiver send an OK reply."
            clientSocket.send(message.upper()+"\r\n")
            recvnoop = clientSocket.recv(1024)
            if len(message) > 512:
                connection.sendall("500 Syntax error, command unrecognized, could it be too long?"+"\r\n") ### length
            elif len(message[5:])>64:
                connection.sendall("501 Syntax error in parameters or arguments, could it be too long?"+"\r\n") ### length
            elif recvnoop[:3] == '250':
                connection.sendall(recvnoop+"\r\n")
            elif recvnoop[:3]== '500':
                connection.sendall("500 Syntax error, command unrecognized"+"\r\n") ### length
            elif recvnoop[:3]== '421':
                connection.sendall("421 csd-mtp Service not available,\n closing transmission channel"+"\r\n")
            else:
                print "other error in noop"
                if len(recvnoop)>512:
                    connection.sendall("500 Other error in NOOP")
                else:
                    connection.sendall(recvnoop)
                print recvnoop

        ###help####
        elif message[0:4].upper() == "HELP":
            clientSocket.send(message.upper()+"\r\n")
            recvhelp = clientSocket.recv(1024)
            if len(message) > 512:
                connection.sendall("500 Syntax error, command unrecognized, could it be too long?"+"\r\n") ### length
            elif len(message[5:])>64:
                connection.sendall("501 Syntax error in parameters or arguments, could it be too long?"+"\r\n") ### length
            elif recvhelp[:3]=='211' or recvhelp[:3]=='214':
                connection.sendall(recvhelp+"\r\n")
            elif recvhelp[:3]== '500':
                connection.sendall("500 Syntax error, command unrecognized"+"\r\n") ### length
            elif recvhelp[:3]== '501':
                connection.sendall("501 Syntax error in parameters or arguments"+"\r\n")
            elif recvhelp[:3]== '503':
                connection.sendall("503  Bad sequence of commands"+"\r\n")
            elif recvhelp[:3]== '421':
                connection.sendall("421 csd-mtp Service not available,\n closing transmission channel"+"\r\n")
            else:
                print "other error rset"
                if len(recvhelp)>512:
                    connection.sendall("500 Other error in HELP")
                else:
                    connection.sendall(recvhelp)
                print recvhelp 
        ###reset####
        elif message[0:4].upper() == "RSET":
            clientSocket.send(message.upper()+"\r\n")
            recvrst = clientSocket.recv(1024)
            if len(message) > 512:
                connection.sendall("500 Syntax error, command unrecognized, could it be too long?"+"\r\n") ### length
            elif len(message[5:])>64:
                connection.sendall("501 Syntax error in parameters or arguments, could it be too long?"+"\r\n") ### length
            elif recvrst[:3]=='250':
                handshake=False
                sendmail=False
                allrecipients=[]
                isData= False
                toSend= False
                sender=""
                canRun=False
                heloDomain=""
                rcptcounter=0
                found=[]
                connection.sendall("250 csd-mtp resetting complete"+"\r\n")
                print "resetting ..."
            elif recvrst[:3]== '500':
                connection.sendall("500 Syntax error, command unrecognized"+"\r\n") ### length
            elif recvrst[:3]== '501':
                connection.sendall("501 Syntax error in parameters or arguments"+"\r\n")
            elif recvrst[:3]== '503':
                connection.sendall("503  Bad sequence of commands"+"\r\n")
            elif recvrst[:3]== '421':
                connection.sendall("421 csd-mtp Service not available,\n closing transmission channel"+"\r\n")
            else:
                print "other error rset"
                if len(recvrst)>512:
                    connection.sendall("500 Other error in RSET")
                else:
                    connection.sendall(recvrst) 
                print recvrst  
        #print select
        else:
            elseresponse = "500 There was an error with the command: "+message+"\nPlease try again (maybe use HELP command?)\r\n"
            if len(elseresponse)>512:
                connection.sendall("500 There was an error with the command \n")
            else:    
                connection.sendall("500 There was an error with the command: "+message+"\nPlease try again (maybe use HELP command?)\r\n")
    else:
        connection.sendall("503 Polite people say HELO first"+"\r\n")

########################




#print "Current server's address: "+Host
#######
HOST = '127.0.0.1'
print "Current server's address: "+HOST+"\r\n"
print "Type a port to use: "
myport= raw_input()
PORT = int(myport)
print "Current server's port: "+myport+"\r\n"
print "Command to connect:"+"\n"+"telnet "+HOST+" "+myport+"\r\n"

#######
sock = socket(AF_INET, SOCK_STREAM)
sock.bind((HOST, PORT))
sock.listen(10)
#####





#infinite loop for clients
while True:
    print  'Waiting for a client...'
    
    connection, client_address = sock.accept()
    try:
        #initiate connection to mail.uoc.gr
        clientSocket = socket(AF_INET, SOCK_STREAM)
        clientSocket.connect((mailserver, 25))
        recv = clientSocket.recv(1024)
        print recv
        if recv[0:3] == '220':
            connection.sendall("220 csd-mtp service ready "+str(datetime.datetime.now())+"\r\n")
            print 'Client connected:', client_address
            while True:
                
                data = connection.recv(1024)
                if data:
                    #connection.sendall ("preaction")
                    action(data)
                    if toSend==True:
                        toSend=False
                        print "in to send"
                        clientSocket.send(endmsg)
                        recv5 = clientSocket.recv(1024)
                        print recv5
                        if recv5[:3]=='250':
                            connection.sendall("250 csd-mtp message was sent successfully"+"\r\n")
                        elif recv5[0:3]== '451':
                            connection.sendall("451 'DATA' action aborted: error in processing"+"\r\n")
                        elif recv5[0:3]== '554':
                            connection.sendall("451 Transaction failed"+"\r\n")
                        else:
                            print "other error in outer data"
                            if len(recv5)>512:
                                connection.sendall("500 Other error in DATA")
                            else:
                                connection.sendall(recv5)
                            print recv5  
                    
                    if isQuit==True:
                        connection.sendall("closing connection...\r\n")
                        
                        print "in quit"
                        clientSocket.send("QUIT\r\n")
                        print "break bond"
                        recv6 = clientSocket.recv(1024)
                        print recv6
                        if recv6[:3]=='221':
                            #resetting all
                            handshake=False
                            sendmail=False
                            allrecipients=[]
                            isData= False
                            toSend= False
                            sender=""
                            canRun=False
                            heloDomain=""
                            rcptcounter=0
                            connection.sendall("221 csd-mtp closing transmission channel")
                            isQuit=False
                            break
                        elif recv6[:3]== '500':
                            isQuit=False
                            connection.sendall("500 Syntax error, command unrecognized"+"\r\n") ### length
                        #connection.close()
                        
                        #continue    
                    
                else:
                    print "in else"
                    break
        elif recv[0:3]=='421':
            connection.sendall("421 csd-mtp service unavailable,\nclosing transmission channel\r\n")
        
    finally:
        connection.close()








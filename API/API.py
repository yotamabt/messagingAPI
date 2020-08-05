from API import app
from flask import request,session,jsonify,render_template_string ,redirect
import sqlite3
from user import User
import datetime
from TableGen import Table
import json

# connect to database
database = sqlite3.connect('MockData.db' ,check_same_thread=False)


# ----------------------------------------------------------------------------------------------------------------------
# helper functions

# User Exists?
def userExists(u):
    sql = "SELECT \'{0}\'in (SELECT username from users)".format(u)
    cur = database.cursor()
    cur.execute(sql)
    res = cur.fetchall()
    return bool(res[0][0])

# Message Exists?
def messageExists(m):
    sql = "SELECT {0} in (SELECT id from messages)".format(m)
    cur = database.cursor()
    cur.execute(sql)
    res = cur.fetchall()
    return bool(res[0][0])

# make a database message row into a dictionary
def createMsgObj(dbrow):
    messageObj = {}
    index = 0
    keys = ["id", "fromuser", "touser", "subject", "body", "datetime", "Unread", "deleted_by_sender",
            "deleted_by_recipient"]
    for key in keys:
        messageObj[key] = dbrow[index]
        index += 1
    return messageObj

#create user
def createUser(username,password):

    #if the user does not exists create the user
    if not userExists(username):
        sql = "INSERT INTO users VALUES (\'{0}\',\'{1}\')".format(username,password)
        database.execute(sql)
        database.commit()
        return {"result": "user {0} was created successfully".format(username)}
    # if the username is in use do nothing and return message
    else:
        return {"result": "username {0} is already in use".format(username)}


# get messages for user function
def getMessagesForUser(user,mode = "ALL"):
    #convert mode to database field
    modedict = {"inbox" : ("touser" , "deleted_by_recipient"),
                "outbox": ("fromuser", "deleted_by_sender") ,
                "unread" : ("touser" , "unread = TRUE AND deleted_by_recipient  ")}
    # init query string
    sql=""

    # all messages query
    if mode == "ALL":
        sql = 'SELECT  * FROM messages WHERE touser = \'{0}\' AND deleted_by_recipient = FALSE ' \
              'OR fromuser = \'{0}\' AND deleted_by_sender = FALSE'.format(user)

    # other modes query
    else:
        sql = 'SELECT  * FROM messages WHERE {1} = \'{0}\' AND {2} = FALSE'.format(user,modedict[mode][0],modedict[mode][1])

    # execute query
    cur = database.cursor()
    cur.execute(sql)

    # make a list of dictionaries from results
    messagelist = []


    for row in cur.fetchall():
        messagelist.append(createMsgObj(row))

    # return final result
    return messagelist

# read message function
def readMessage(user,id):
    # check if message exists - if not return an error message
    if not messageExists(id):
        return {"error":"message not found"}

    # if message exists and the user is the recipient set its unread  value to false, and fetch it from the database

    sql = "UPDATE messages SET unread = FALSE WHERE id = {0} and touser = \'{1}\'".format(id,user)
    cur = database.cursor()
    cur.execute(sql)
    database.commit()
    sql = "SELECT * FROM messages WHERE id = {0}".format(id)
    cur = database.cursor()
    cur.execute(sql)
    res = cur.fetchall()
    finalObj = createMsgObj(res[0])

    # check if the user deleted the message
    if finalObj["fromuser"] == user and bool(finalObj["deleted_by_sender"]) or finalObj["touser"] == user and bool(finalObj["deleted_by_recipient"]):
        return {"error": "message was deleted"}
    if user not in [finalObj["fromuser"] , finalObj["touser"] ]:
        return {"message": "you are not authorized to read this message"}
    # return the message
    return createMsgObj(res[0])

# send Message function
def sendMessage(fromuser,touser,subject,body):
    # init a Message Object
    messageObj = {}

    # if both users exist
    if userExists(fromuser) and userExists(touser):

        # get the time
        nowstr = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        # create insert statement
        sql = '''insert INTO messages(fromuser,touser,subject,body,created,unread,deleted_by_sender,deleted_by_recipient)
            VALUES
        ('{0}','{1}','{2}','{3}','{4}',TRUE,FALSE,FALSE)
            
            '''.format(fromuser,touser,subject,body,nowstr)

        # execute
        cur = database.cursor()
        cur.execute(sql)
        database.commit()

        # get the row id of the message
        id = cur.lastrowid

        # get the message from database
        cur.execute("SELECT * FROM messages WHERE rowid = {0}".format(id))
        res = cur.fetchall()

        #create Object

        messageObj = createMsgObj(res[0])


    # if sender is not a user append an error to the response
    if not userExists(fromuser):
        if "errors" not in messageObj.keys():
            messageObj["errors"] = []
        messageObj["errors"].append("sender with the username {0} does not exist".format(fromuser))

    # if recipient is not a user append an error to the response
    if not userExists(touser):
        if "errors" not in messageObj.keys():
            messageObj["errors"] = []
        messageObj["errors"].append("recipient with the username {0} does not exist".format(touser))
    return messageObj




def deleteMessage(user ,mid):
    # check if message exists - if not return an error message
    if not messageExists(mid):
        return {"error":"message not found"}

    # sql query to get the users and delete statuses of the message
    sql = "SELECT fromuser ,touser ,deleted_by_sender,deleted_by_recipient FROM messages WHERE id = {0}".format(mid)
    cur = database.cursor()
    cur.execute(sql)
    res = cur.fetchall()

    #set a list with the usernames and delete statuses
    senderAndRecipient = [res[0][0] , res[0][1]]
    deleteStatuses = [bool(res[0][2]) , bool(res[0][3])]

    #check if the user is the sender or the recipient and if so chage the corresponding delete status
    if user == senderAndRecipient[0]:
        cur.execute("UPDATE messages SET deleted_by_sender = TRUE WHERE id = {0}".format(mid))
        database.commit()
        deleteStatuses[0] = True
    elif user == senderAndRecipient[1]:
        cur.execute("UPDATE messages SET deleted_by_recipient = TRUE WHERE id = {0}".format(mid))
        database.commit()
        deleteStatuses[1] = True

    # if the user is not the sender or recipient of this message end the operation.
    elif user not in senderAndRecipient:
        return {"error":"you are no authorized to delete this message"}

    # if both users delete the message , delete the message from the database
    if deleteStatuses[0] and deleteStatuses[1]:
        cur.execute("DELETE FROM messages WHERE id = {0}".format(mid))
        database.commit()

    # return success message
    return {"message":"message number {0} was successfully deleted".format(mid)}




#----------------------------------------------------------------------------------------------------------------------



#set secret key
app.secret_key = "SECRET_KEY"


#----------------------------------------------------------------------------------------------------------------------
#routes:

#sign in route
@app.route("/signup", methods = ["POST"])
def signup():
    data = request.get_json()
    return(jsonify(createUser(data["username"],data["password"])))

#login route
@app.route("/login", methods = ["POST"])
def login():
    # create a User object using the authorization headers
    u = User(database,request.authorization.username,request.authorization.password)
    # if its a valid user update the session (create cookie)
    if u.authorized:
        session["username"] = u.username
        return jsonify({"username":u.username, "response": "login success" })
    # if its not a valid user update the session (remove any logged in user)
    else:
        session.pop("username" , None)
        return jsonify({"message": u.username, "response": "login failure"})



#logout route
@app.route("/logout", methods = ["POST"])
def logout():
    #update the session (remove any logged in user)
    session.pop("username", None)
    return jsonify({"message": "you are now logged out" })


@app.route("/my-inbox")
def myInbox():
    #get messages from database
    if "username" in session.keys():
        inboxlist = getMessagesForUser(session["username"],mode="inbox")
        #if there are no messages
        if(len(inboxlist) == 0):
            return jsonify({"message": "inbox empty"})
        return jsonify(inboxlist)
    #if not logged in
    else:
        return jsonify({"message": "you must log in to view inbox items"})

@app.route("/my-outbox")
def myoutbox():
    #get messages from database
    if "username" in session.keys():
        outboxlist = getMessagesForUser(session["username"],mode="outbox")
        #if there are no messages
        if(len(outboxlist) == 0):
            return jsonify({"message": "outbox empty"})
        return jsonify(outboxlist)
    #if not logged in
    else:
        return jsonify({"message": "you must log in to view outbox items"})


@app.route("/my-unread-messages")
def myUnreadMessages():
    # get messages from database
    if "username" in session.keys():
        outboxlist = getMessagesForUser(session["username"], mode="unread")
        # if there are no messages
        if (len(outboxlist) == 0):
            return jsonify({"message": "no unread messages"})
        return jsonify(outboxlist)
    # if not logged in
    else:
        return jsonify({"message": "you must log in to view unread messages"})

# send message route
@app.route("/send-message" , methods = ["POST"])
def sendMessageRoute():

    #get the payload
    msgData = request.get_json()
    res = None

    #check if user is logged in
    if "username" in session.keys():
        try:

            # try sending the message and saving the output in the res variable
            res = sendMessage(session["username"], msgData["touser"], msgData["subject"], msgData["body"])
            return jsonify(res)
        # any incorrect input will be caught here
        except:
            return jsonify({"error": "invalid or incomplete data"})

    # if the user is not logged in
    else:
        return jsonify({"message": "you must log in to send messages"})



    return res

@app.route("/delete-message", methods = ["DELETE"])
def deleteMessageRoute():
    # get the request body
    data = request.get_json()
    # check username
    if "username" in session.keys():
        # any incorrect input will be caught here
       try:
           return deleteMessage(session["username"], data["id"])
       except:

           return {"error": "invalid or incomplete data"}

    # if not logged in
    else:
        return jsonify({"message": "you must log in to delete a message"})

@app.route("/read-message", methods = ["GET"])
def readMessageRoute():
    # get the request body
    data = request.get_json()
    # check username
    if "username" in session.keys():
        # any incorrect input will be caught here
       try:
           return readMessage(session["username"], data["id"])
       except :
           return {"error": "invalid or incomplete data"}

    # if not logged in
    else:
        return jsonify({"message": "you must log in to read a message"})

# Browser login
@app.route("/visual/login",methods=["GET","POST"])
def visualLogin():
    # render login form if the method is GET
    if request.method == "GET":
        html = '''
            <html>
            <head>

            </head>
            <body>
            <form method="POST" action="/visual/login">
            <label>username: <input type="text" name="username"  required></label>
            <label>password: <input type="password" name="password"  required></label>
            <button type="submit">Login</button>
            </form>
            </body>


            </html>
                '''
        return render_template_string(html)

    # login if  the method is POST
    elif request.method == "POST":
        # create a User object using the authorization headers

        u = User(database, request.form["username"], request.form["password"])
        # if its a valid user update the session (create cookie)
        if u.authorized:
            session["username"] = u.username
            return redirect('/visual/messages')
        # if its not a valid user update the session (remove any logged in user)
        else:
            session.pop("username", None)
            return render_template_string("<h3>LOGIN FAILED</h3>")

@app.route("/visual/messages", methods = ["GET"])
def visualMessages():
    # get the request body
    # check username
    if "username" in session.keys():
        # make an inbox and outbox objects
        inbox = getMessagesForUser(session["username"],mode="inbox")
        outbox = getMessagesForUser(session["username"],mode="outbox")

        #if one of the objects is empty make it an object that tablegen can handel
        if len(inbox) == 0 :
            inbox = [{"Messages" : "None"}]
        if len(outbox) == 0 :
            outbox= [{" No Messages" : ""}]

        #style string
        style = '''<style>
                table  {
                border:solid;
                border-collapse: collapse;
                border-width: 1px;
                border-color :rgb(202, 202, 202);
                font-size: medium;
                
                
                    }
                    h3{
                        width:85%; 
                margin-left:7.5%; 
                margin-right:7.5%; 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                text-align: center;
                    }
                    th,td {
                
                        font-size: 15px;
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    border-top:solid;
                border-collapse: collapse;
                border-width: 1px;
                border-color :rgb(202, 202, 202);
                    }
                    th{
                        text-align: left;
                        height: 80px;
                        vertical-align: middle;
                        position: sticky;
                        padding-right: 20px;
                        background-color: rgb(66, 0, 61);
                        top:0;
                    }
                   
                    
                    
              
                thead{
                    background-color: rgb(66, 0, 61);
                    color: mintcream;
                }
                

                
                
                </style> '''
        # take html tables from tablegen (another package I made ) and cut only the table part from the full HTML
        inboxHTML = Table(inbox,index = True,HTMLtableclass="msg").HTMLString.split("<body>")[1].split("</body>")[0]
        outboxHTML = Table(outbox,index = True,HTMLtableclass="msg").HTMLString.split("<body>")[1].split("</body>")[0]

        # build a final HTML string
        html = style + "<h3> {0}'s Messages</h3>".format(session["username"]) + "<br><br><h3>Inbox:</h3> <br><br>" + inboxHTML + \
               "<br><br><h3>Outox:</h3> <br><br>"+ outboxHTML

        # render page
        return render_template_string(html)

    else:
        return render_template_string("<h3>MUST BE LOGGED IN TO VIEW THIS PAGE<h3>")

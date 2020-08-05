# Messaging API

This is a very simple Messaging API written in flask.it enables signup , log in getting inbox , outbox and unread messages and reading and deleting message by id.

all the users and messages data is stored in an sqlite database.

there are test users like user1:pass1 ,user2:pas2....user8:pass8

the api has also two routes that enable login and viewing the messages for the logged in user in HTML format as a table .

all the security practices in this API are a joke (passwords as plain text etc..) and sould not be used in any production situation , but they are good enough for testing the API.

## routes

### POST /signup
this route is used to create a new user , it takes an in put of username and password in the request body:

``` 
{
"username": "user6",
"password": "pass6"
}
```

if the user name is not in use the response will be:

```
{
    "result": "user user6 was created successfully"
}
```
and the user will be saved in the database.

if the user name is in use the response will be:

```
{
    "result": "username user8 is already in use"
}
```

### POST /login
this route is used to login an existing user.

**this route is required for all other routes except signup to work!**

this route will take the username and password from the authorization header using basic Authentication
postman request sshould be sent like this:
![postman auth](https://i.ibb.co/qr447hF/postman-auth.jpg)

if the username and password combination is valid, the response will be
```
{
    "response": "login success",
    "username": "user6"
}
```
if the username and password combination is invalid, the response will be:
```
{
    "message": "none",
    "response": "login failure"
}
```

### POST /logout
this route is used logout any logged in user.

response:
``` 
{
    "message": "you are now logged out"
}
```

### GET /my-inbox
this route is used to get all inbox messages for the logged in user.

if there is a logged in user the respone will be a list of message objects:
``` 
[
    {
        "Unread": 0,
        "body": "Hi user6, this is user5,How are you?",
        "datetime": "03-08-2020 20:15",
        "deleted_by_recipient": 0,
        "deleted_by_sender": 0,
        "fromuser": "user5",
        "id": 5,
        "subject": "This is a massege from user5",
        "touser": "user6"
    },
    {...
]
```
if there are no messages the response will be:
```
{
    "message": "inbox empty"
}
```

if there is no logged in user the response will be:

```
{
    "message": "you must log in to view inbox items"
}
```

### GET /my-outbox
this route is used to get all outbox messages for the logged in user.

if there is a logged in user the respone will be a list of message objects:

``` 
[
    {
        "Unread": 0,
        "body": "Hi user5, this is user6,How are you?",
        "datetime": "03-08-2020 20:15",
        "deleted_by_recipient": 0,
        "deleted_by_sender": 0,
        "fromuser": "user6",
        "id": 5,
        "subject": "This is a massege from user5",
        "touser": "user5"
    },
    {...
]
```

if there are no messages the response will be:

```
{
    "message": "outbox empty"
}

```

if there is no logged in user the response will be:

```
{
    "message": "you must log in to view outbox items"
}
```
### GET "/my-unread-messages
this route is used to get all unread messages for the logged in user.

if there is a logged in user the respone will be a list of message objects:

``` 
[
    {
        "Unread": 1,
        "body": "Hi user6, this is user5,How are you?",
        "datetime": "03-08-2020 20:15",
        "deleted_by_recipient": 0,
        "deleted_by_sender": 0,
        "fromuser": "user6",
        "id": 5,
        "subject": "This is a massege from user5",
        "touser": "user6"
    },
    {...
]
```

if there are no messages the response will be:

```
{
    "message": "no unread messages"
}

if there is no logged in user the response will be:

```
{
    "message": "you must log in to view unread items"
}
```
### POST /send-message
this route will send a message from the logged in user it takes three values in the request value:
```
{
"touser":"user4",
"subject":"hi man",
"body":"sup bro?"
}
```
if the request is successful the response will be the message object:
```
{
    "Unread": 1,
    "body": "sup bro?",
    "datetime": "2020-08-05 01:01",
    "deleted_by_recipient": 0,
    "deleted_by_recipientr": 0,
    "fromuser": "user2",
    "id": 11,
    "subject": "hi man",
    "touser": "user4"
}
```

the time stamp for the message will be the current time and the boolean values for unread , deleted_by_recipient and deleted_by_recipient will be set automatically .

if the user is not logged in the response will be :
```
{
"message": "you must log in to send messages"
}
```
if there is a value missing , or wrong datatype in the input , the response will be:
```
{
"error": "invalid or incomplete data"
}
```
if the recipient does not exist the response will be :
```
{
    "errors": [
        "recipient with the username incorrectuser does not exist"
    ]
}
```

### GET /read-message
this route will get a message by id and change its unread status if the logged in user is the recipient, it takes just the id in the request body.
```
{
"id":11
}
```
if the request is successful the response will be the message object:
```
{
    "Unread": 0,
    "body": "sup bro?",
    "datetime": "2020-08-05 01:01",
    "deleted_by_recipient": 0,
    "deleted_by_recipientr": 0,
    "fromuser": "user2",
    "id": 11,
    "subject": "hi man",
    "touser": "user4"
}
```

if the user is not logged in the response will be :
```
{
"message": "you must log in to read messages"
}
```
if there is a value missing , or wrong datatype in the input , the response will be:
```
{
"error": "invalid or incomplete data"
}
```
if the message does not exist the response will be
```
{
"error":"message not found"
}
```
if the message exists in the data base but was deleted by the user:
```
{
"error": "message was deleted"
}
```
if the user is not the sender or recipient:
```
{
    "message": "you are not authorized to read this message"
}
```

### DELETE /delete-message
this route will delete a message by id it will change the deletion status field for the sender and recipient and if both are set to True , it will delete the message from the database. it takes only the id in the request body
```
{
"id":11
}
```
if the request is successful the response will be :
```
{
    "message": "message number 11 was successfully deleted"
}
```

if the user is not logged in the response will be :
```
{
"message": "you must log in to read messages"
}
```
if there is a value missing , or wrong datatype in the input , the response will be:
```
{
"error": "invalid or incomplete data"
}
```
if the message does not exist the response will be
```
{
"error":"message not found"
}
```
if the user is not the sender or recipient:
```
{
"error":"you are no authorized to delete this message"
}
```

### GET /visual/login
this route is for browser use, it will render an HTML login from: 
![login screen](https://i.ibb.co/j5K73hd/login.png)

if the lgoin is successful the user will be redirected to /visual/messages

### GET /visual/messages
this route renderes html tables from the inbox and outbox of the logged in user and render a page that views them both.
![tables](https://i.ibb.co/chw6G5r/tables.png)

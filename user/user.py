import datetime


#helper function to validate the user
#(All passwords are stored as plain text, really bad practice , but it will work for testing the api)
def validate(d,u,p):
    # look for the user in the database
    sql = "SELECT * FROM users WHERE username = \'{0}\'".format(u)
    cur = d.cursor()
    cur.execute(sql)
    res = cur.fetchall()

    # if the user does not exist return False
    if len(res) == 0:
        return False
    # if the user exists but the password is incorrect return False
    elif len(res) == 1 and p != res[0][1]:
        return False
    # if the user exists and the password is correct return True
    elif len(res) == 1 and p == res[0][1]:
        return True





#User class
class User:
    def __init__(self ,database, username,password):

        #check if the credentials are correct
        self.authorized = validate(database,username,password)

        #if they are correct init the user
        if self.authorized:
            self.username = username
            self.loginTime = datetime.datetime.now()

        #if they are incorrect have the user contain an error message
        else:
            self.username = "none"
            self.error = "this user does not exist or the password is incorrect"





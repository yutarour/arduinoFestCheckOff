#has updated check off options
import gradio as gr
import json
import random
import datetime
import ngrok
import argparse as ap
from dotenv import load_dotenv
import os
import logging

###################################
ARDUINOEND = datetime.datetime(2023,12,15,14,50)

#if set to true will use ngrok's tunnels to publish the webpage
NGROK_START = True

#multiple registers at once blocked when true
CHECKDOUBLEDIPPING = True

#check for projects with the same name
CHECKSAMEPROJECTNAME = True
###################################

parser = ap.ArgumentParser()
parser.add_argument("-p","-production",type=bool)
logging.basicConfig(level=logging.INFO)

load_dotenv()

NGROK_KEY = os.getenv("NGROK_KEY")
NGROK_DOMAIN = os.getenv("NGROK_DOMAIN")

database = {}
#select which database is going to be used. prod is the production database and should not be used for testing purposes
args = parser.parse_args()

#if you include -p arg
if args.p:
    DATABASE_DIRECTORY = "./proddb.json"
else:
    DATABASE_DIRECTORY = "./testdb.json"

#saves the database
def saveDB():
    with open(DATABASE_DIRECTORY,'w') as file:
        json.dump(database,file,indent=4)

#function that loads the database (not used, but could be added to the teacher UI as a feature)
def loadDB():
    global database
    with open(DATABASE_DIRECTORY,'r') as file:
        database = json.load(file)

#function to find the user, return based on their ID
def findUser(id:int):
    for user in database["users"]:
        if user["id"] == id:
            return user
    return None

#function to add people to the queue. 
def addCheckOff(id:str,projectNum:str,afterSchool:bool):
    #check to see if the id is a number
    try:
        int(id)
    except ValueError:
        return "### Invalid ID"
    
    user = findUser(int(id))
    if user == None:
        return "### You seem to not have a ID. Check the ID or get one."
    
    #user exists
    else:
        #check if user is already in queue
        if CHECKDOUBLEDIPPING:
            for queue in database["checkoffs"]:
                if queue["id"] == user["id"]:
                    return "### You can not sign up twice."
        
        if CHECKSAMEPROJECTNAME:
            for project in user["checkoffs"]:
                if project["projectNum"].lower().lstrip().rstrip() == projectNum.lower().lstrip().rstrip():
                    return "### You can not sign up for checkoffs with the same project name twice!"
                
        #add a 0 to the checkoff list addition so that they show up in the 
        if afterSchool:
            user["periods"].append(0)

        database["checkoffs"].append({
            "name":user["name"],
            "id":user["id"],
            "periods":user["periods"],
            "currentProject":projectNum
        })
        saveDB()
        return "### You have been added!"

#function to load the queue. Takes authentication that is checked against the database. 
#the auth feature is not used, but it may be used in the auto-reloading queue system which takes more resources
#than the usual auth therefore probably should be locked down
def loadQueue(period:int,authent:str=None):
    
    try:
        int(period)
    except ValueError:
        return "## Please select a period!"
    except TypeError:
        return "## Please select a period!"

    if period == '':
        return "## Please select a period!"
    
    baseMarkDown = "# Current queue: \n"

    #insert the time left
    duration = ARDUINOEND-datetime.datetime.now()

    days, seconds = duration.days, duration.seconds
    hours = days * 24 + seconds // 3600
    minutes = (seconds % 3600) // 60

    baseMarkDown+=f"### It is {datetime.datetime.now().strftime("%A, %B %d %Y, %H:%M:%S")}\n### You have {days} days, {hours} hours, and {minutes} minute(s) left!\n"
    if authent == None:
        counter = 1
        for checkoff in database["checkoffs"]:
            #if the user is in the period the user asked for
            if int(period) in checkoff["periods"]:
                baseMarkDown+= f"## {counter}. {checkoff['name']} | {checkoff['currentProject']}\n"
                counter+=1
    
    elif authent in database["teachers"]:
        counter = 1
        for checkoff in database["checkoffs"]:
            #if the user is in the period the user asked for
            if int(period) in checkoff["periods"]:
                baseMarkDown+= f"## {counter}. {checkoff['name']} | {checkoff['currentProject']}\n"
                counter+=1
    
    else:
        return "# Not authorized!"


    return baseMarkDown

#the funciton that is callable by students to remove themselves from the queue used in case of a mistake
def removeUserFromQueue(userid:str):
    #check to see if the id is a number
    try:
        int(userid)
    except ValueError:
        return "### Invalid ID"
    
    for index,user in enumerate(database["checkoffs"]):
        if user["id"] == int(userid):
            database["checkoffs"].pop(index)
            saveDB()
            return "### You have been successfully been removed"
    
    return f"### ID {userid} was not found in the checkoff list."

#the function that adds the user to the database of users. Generates a unique 4 digit ID for them which is random
#additional element can be added to make the numbers something that is easier to remember. (probably should have done that)
def registerUser(name,periods):
    for user in database["users"]:
        if name.lower() == user["name"].lower():
            return "## There is already a user with that name."
    
    id = random.randint(1000,9999)
    while findUser(id) != None:
        id = random.randint(1000,9999)
    
    if len(periods) == 0:
        return "Please enter periods and try again"

    #user only has either ent or csp
    if len(periods) == 1:
        database["users"].append({
                "id":id,
                "name":name,
                "periods":[int(periods[0])],
                "checkoffs":[]
            })
    
    #user has both ent and csp
    if len(periods) == 2:
        database["users"].append({
                "id":id,
                "name":name,
                "periods":[int(periods[0]),int(periods[1])],
                "checkoffs":[]
            })
    saveDB()
    return f"# ID: {id}\n### Write this ID Down somewhere e.g. Arduino packet so that you won't forget."

#function that is in the register tab that removes users from the database based on id.
#It also removes them from the queue to avoid a un-deletable user in the queue
def unregisterUser(userid):
    try:
        int(userid)
    except ValueError:
        return "### Invalid ID"

    #remove person from user list
    for index,user in enumerate(database["users"]):
        if user["id"] == int(userid):
            database["users"].pop(index)
    
    #remove person from queue
    for index,user in enumerate(database["checkoffs"]):
        if user["id"] == int(userid):
            database["checkoffs"].pop(index)
    saveDB()
    return "### Removed user "+userid

#display student info this is for teachers only and is useful for looking up ids from names.
def viewStudentInfo(teacherauth):
    if teacherauth in database["teachers"]:
        basemd = "## Students:\n"
        for user in database["users"]:
            basemd+=f"### - Name: {user['name']}, ID: {user['id']}, Periods: {user['periods']}\n"
        return basemd
    else:
        logging.info("Failed login attempt: "+teacherauth)
        return "# You are not authorized to view this information!"

#function that is used by the teacher view to check students off. Takes the checkbox group and check students off and adds it to the log
def checkOffUser(id:list,period:int,auth:str): 
    #id is list that looks like: [['0. c, Project: a', 1336], ['1. b, Project: a', 8967], ['2. d, Project: a', 6770]]
    if auth in database["teachers"]:
        #user is authorized to check off
        retMsg = ""
        for ticked in id:
            for index,checkoff in enumerate(database["checkoffs"]):
                #if the user is in the period the user asked for
                if int(period) in checkoff["periods"]:
                    if ticked == checkoff["id"]:
                        database["checkoffs"].pop(index)
                        #add details to the userdb on when and what they finished
                        for useridx,user in enumerate(database["users"]):
                            if user["id"] == ticked:
                                #save the info in their user profile
                                database["users"][useridx]["checkoffs"].append({
                                    "time":datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
                                    "projectNum":checkoff["currentProject"],
                                    "authorized":auth
                                })
                                retMsg+=f"### Checked off user {ticked} off\n"
                                logging.info(f"{auth} has checked {ticked} off")
                                break   
                                #die after the first one
        saveDB()
        return {checkoffSubmitStatus:retMsg,checkoffOutput:checkBoxQueue(period,auth)[checkoffOutput]}
    
    else:
        return {checkoffSubmitStatus:"# Not authorized",checkoffOutput:gr.CheckboxGroup(choices=None)}

#new load with checkbox used specifically for the teacher checkoff feature
#special function to handle the teacher check off queue display to be a checkbox
def checkBoxQueue(period:str,teacherauth:str):
    if period == []:
        return {checkoffOutput:gr.CheckboxGroup(choices=None),checkoffSubmitStatus:"## Please select a period!"}
    if period == '':
        return {checkoffOutput:gr.CheckboxGroup(choices=None),checkoffSubmitStatus:"## Please select a period!"}

    choices = []
    counter = 1
    if teacherauth in database["teachers"]:
        for checkoff in database["checkoffs"]:
            #if the user is in the period the user asked for
            if int(period) in checkoff["periods"]:
                choices.append((f"{counter}. {checkoff['name']}, Project: {checkoff['currentProject']}",checkoff["id"]))
                counter+=1
    else:
        return {checkoffOutput:gr.CheckboxGroup(choices=None),checkoffSubmitStatus:"# Not authorized"}
    #returns to two components. the checkboxes, which get auto-updated with the choices and a status message (markdown)
    return {checkoffOutput:gr.CheckboxGroup(choices=choices),checkoffSubmitStatus:"## Success"}
gr.CheckboxGroup

with gr.Blocks(title="ArduinoFest 2023 Sign offs",analytics_enabled=False) as container:
    gr.Markdown("## Arduinofest Signups")

    #the signup box. Takes id (4 digit integer) and the project name which is a string. 
    #the strings may not be the same. Additionally, there is a afterSchool checkbox that when ticked will add them temporarely to the after school queue.
    with gr.Tab("Sign Up For Check off"):
        idnum = gr.Textbox(label="Enter ID number here")
        projectnum = gr.Textbox(label="Enter which project you are on")
        afterSchool = gr.Checkbox(label="Check if After school or Before school")
        idsubmit = gr.Button("Submit")
        statusOut = gr.Markdown("### Status")
    
    idsubmit.click(addCheckOff,inputs=[idnum,projectnum,afterSchool],outputs=statusOut)

    #used when user may have accidentally added themselves to the list or recognize that they need more time.
    with gr.Tab("Remove me from the List"):
        removeid = gr.Textbox(label="Enter ID number here")
        removesubmit = gr.Button("Submit")
        removeStatus = gr.Markdown("### Status")

    removesubmit.click(removeUserFromQueue,inputs=removeid,outputs=removeStatus)

    #loads the student queue view. 0th is for before/after school
    with gr.Tab("View Queue"):
        queueselect = gr.Dropdown([0,1,2,3,4,5,6,7],label="Period")
        queue = gr.Button("Search")
        queuestatus = gr.Markdown("### Please search",)
    
    queue.click(loadQueue,inputs = queueselect, outputs = queuestatus)
    queueselect.change(loadQueue,inputs = queueselect, outputs = queuestatus)

    with gr.Tab("Register"):
        gr.Markdown("## Register for a ID number")
        #adds user to the database. 
        with gr.Tab("Add"):
            gr.Markdown("### Add yourself from the database")
            gr.Markdown("### Write your full first, last name. if you have a nickname, write it with a / after your name. e.g. John Smith/Johnny")
            name = gr.Textbox(label="Name (First Last)")
            addperiods = gr.Dropdown([1,2,3,4,5,6,7],multiselect=True,max_choices=2,label="Periods: both CSP and Ent.")
            useraddsubmit = gr.Button("Submit")
            addUserOut = gr.Markdown()

            useraddsubmit.click(registerUser,inputs=[name,addperiods],outputs=addUserOut)

        #remove user from the database, used when they may have accidentally mis-entered their period or name
        with gr.Tab("Remove"):
            gr.Markdown("### Remove yourself from the database")
            userremoveid = gr.Textbox(label="id")
            userremovesubmit = gr.Button("Submit")
            removeUserOut = gr.Markdown("# Warning: This will clear you from all of the checkoff queues and delete your info")

            userremovesubmit.click(unregisterUser,inputs=userremoveid,outputs=removeUserOut)

    #forgot ID can be implemented (optional)
    #with gr.Tab("Forgot ID"):
    #    gr.Markdown("## You can use your first, last name and period to search for your ID")

    #teacher operations tab
    with gr.Tab("Teacher Checkoff"):
        gr.Markdown("### Place for teachers to check off students.")
        with gr.Accordion("Credentials"):
            #credential input. Put inside of a acordion so it may be hidden to hide the credentials
            gr.Markdown("### Enter your credentials here")
            authent = gr.Textbox(label="Enter teacher key here: ")

        with gr.Tab("View students"):
            viewStudents = gr.Button("Submit")
            with gr.Accordion("Students"):
                viewStudentsOut = gr.Markdown()
            #when button is pressed, it will load all of the currently existing students in.
            viewStudents.click(viewStudentInfo,inputs=authent,outputs=viewStudentsOut)

        with gr.Tab("Check off students"):
            #show period selection box auto-reloads the queue when different period is selected
            checkoffperiod = gr.Dropdown([0,1,2,3,4,5,6,7],label="Period")
            #manual queue load button
            checkoffLoadQueue = gr.Button("Load Queue")
            
            checkoffSubmitStatus = gr.Markdown()
            #checkoff target
            #show queue, target checkoff boxes
            checkoffOutput = gr.CheckboxGroup(interactive=True,label="Check off students")
            #submit check off button
            checkoffSubmit = gr.Button("Submit check offs")
            
            #when user changes the period, auto-reload the queue
            checkoffperiod.change(checkBoxQueue,inputs=[checkoffperiod,authent],outputs=[checkoffOutput,checkoffSubmitStatus])
            #when user clicks the load button, re-load the queue
            checkoffLoadQueue.click(checkBoxQueue,inputs=[checkoffperiod,authent],outputs=[checkoffOutput,checkoffSubmitStatus])
            #when user clicks submit checkoffs
            checkoffSubmit.click(checkOffUser,inputs=[checkoffOutput,checkoffperiod,authent], outputs=[checkoffSubmitStatus,checkoffOutput])

        #TODO: Add auto-reload natively to the program to avoid the selenium based id-checking auto-reload system
        #with gr.Tab("AutoReload Queue") as aqr:
        #    autoqueueselect = gr.Dropdown([0,1,2,3,4,5,6,7],label="Period")
            #autoqueue = gr.Button("Search")
        #    autoqueuestatus = gr.Markdown("### Please search",)

            #aqc = autoqueue.click(loadQueue,inputs = [autoqueueselect,authent], outputs = autoqueuestatus,every=5)
        #autoqueueselect.change(loadQueue,inputs = [autoqueueselect,authent], outputs = autoqueuestatus,every=5,cancels=[dep])
            

if __name__ == "__main__":
    #load persistent database to recover data
    loadDB()

    if NGROK_START:
        if NGROK_KEY == None or NGROK_DOMAIN == None:
            print("You need key and a domain to host this site on a static domain!!! Make sure to add it to the .env file.")
            quit()
        listener = ngrok.forward(
            addr="localhost:80",
            authtoken = NGROK_KEY,
            domain= NGROK_DOMAIN
        )
    #enable queue (needed for auto-reload feature once implemented)
    #container.queue(concurrency_count=5, max_size=5)
    #launch the server on port 80, http
    container.launch(server_port=80,favicon_path="favicon.ico")

#Remarks: Hosted on a computer which has a tunnel via ngrok to a free-static domain from ngrok (domain remains static so that I can run code from a different computer and it still will work and have the same IP)
#BTW: The URL was tinyurl'd in order to make it easier to type.

#Remarks: Hosted on a computer which has a tunnel via ngrok to a free-static domain from ngrok (domain remains static so that I can run code from a different computer and it still will work and have the same IP)
#BTW: The URL was tinyurl'd in order to make it easier to type.
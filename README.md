# Arduinofest Checkoff Program
#### A python program based on gradio meant to help with Tesla STEM HS's ArduinoFest checkoff system

## Required files/items:
- ngrok account and a domain, and ngrok token

## how to set up
- copy this into a file. Name the file .env and copy paste the following
```
NGROK_KEY=
NGROK_DOMAIN=
```
- put your ngrok authtoken after the NGROK_KEY after the equal and the domain after the NGROK_DOMAIN
```
#example config
NGROK_KEY=123456712308712974huhjkaldsfhwilueyl
NGROK_DOMAIN=example.ngrok.io
```

- make a file called ```proddb.json``` in the same folder as startServer and paste the contents of ```basejson.json``` into it. This will be the production database when the program is started with the production argument. This file will not be pushed to git for privacy reasons. (included in .gitignore)

## How to start
- the program has two modes. Production mode and Test mode.
- run startServer.py with the -p arg to start the script in production mode. This will use the production database.
```python startServer.py -p``` If no args are provided it will start in test mode and use the testdb.json file as its database.

## pre-configuration before you start
- Right under the imports there exists a block of code seperated by pound symbols.
```python
###################################
ARDUINOEND = datetime.datetime(2023,12,15,14,50)

#if set to true will use ngrok's tunnels to publish the webpage
NGROK_START = True

#multiple registers at once blocked when true
CHECKDOUBLEDIPPING = True

#check for projects with the same name
CHECKSAMEPROJECTNAME = True
###################################
```
- These can be modified. The descriptions are commented, but here is some more description.
- ARDUINOEND: The date at which arduinoFest will end. Used for the countdown. Please set to the end of ArduinoFest. In the example above, it is set to December 15 2023 at 2:50 pm (2023/12/15/14:50 YY/MM/DD HH:MM)
- NGROK_START: Whether to serve the signup page through ngrok. You have to have a .env with the details entered. See steps for .env above in how to setup
- CHECKDOUBLEDIPPING: Blocks double registerations from the same id.
- CHECKSAMEPROJECTNAME: Blocks the projects with the same name from the same person. Requires a different project name every time.


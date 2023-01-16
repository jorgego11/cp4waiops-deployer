
import requests
from requests.auth import HTTPBasicAuth
import json
import datetime
import time
import random
import os
from functions import *
import discord
from discord.ext import commands
from urllib.parse import quote_plus
from threading import Thread

# ----------------------------------------------------------------------------------------------------------------------------------------------------
# GET VARIABLES
# ----------------------------------------------------------------------------------------------------------------------------------------------------
DEMO_EVENTS_MEM=os.environ.get('DEMO_EVENTS_MEM')
DEMO_EVENTS_FAN=os.environ.get('DEMO_EVENTS_FAN')
DEMO_LOGS=os.environ.get('DEMO_LOGS')
LOG_ITERATIONS=int(os.environ.get('LOG_ITERATIONS'))
LOG_TIME_FORMAT=os.environ.get('LOG_TIME_FORMAT')
LOG_TIME_STEPS=int(os.environ.get('LOG_TIME_STEPS'))
LOG_TIME_SKEW=int(os.environ.get('LOG_TIME_SKEW'))
LOG_TIME_ZONE=int(os.environ.get('LOG_TIME_ZONE'))

EVENTS_TIME_SKEW=int(os.environ.get('EVENTS_TIME_SKEW'))

INSTANCE_NAME=os.environ.get('INSTANCE_NAME')
if INSTANCE_NAME == None:
    INSTANCE_NAME="CP4WAIOPS"


METRIC_TIME_SKEW=int(os.environ.get('METRIC_TIME_SKEW'))
METRIC_TIME_STEP=int(os.environ.get('METRIC_TIME_STEP'))
METRICS_TO_SIMULATE_MEM=str(os.environ.get('METRICS_TO_SIMULATE_MEM')).split(';')
METRICS_TO_SIMULATE_FAN_TEMP=str(os.environ.get('METRICS_TO_SIMULATE_FAN_TEMP')).split(';')
METRICS_TO_SIMULATE_FAN=str(os.environ.get('METRICS_TO_SIMULATE_FAN')).split(';')


# READ ENVIRONMENT VARIABLES
DEBUG_ME=os.environ.get('DEBUG_ME',"False")
ACTIVE=os.environ.get('ACTIVE',"False")
DISCORD_BOT_TOKEN=os.environ.get('DISCORD_BOT_TOKEN',"None")
DISCORD_BOT_NAME=os.environ.get('DISCORD_BOT_NAME',"demo")
DISCORD_BOT_PREFIX=os.environ.get('DISCORD_BOT_PREFIX',"/")
ITERATE_ELEMENT=os.environ.get('ITERATE_ELEMENT')
WEBHOOK_DEBUG=os.environ.get('WEBHOOK_DEBUG')




print ('*************************************************************************************************')
print ('*************************************************************************************************')
print ('         __________  __ ___       _____    ________            ')
print ('        / ____/ __ \\/ // / |     / /   |  /  _/ __ \\____  _____')
print ('       / /   / /_/ / // /| | /| / / /| |  / // / / / __ \\/ ___/')
print ('      / /___/ ____/__  __/ |/ |/ / ___ |_/ // /_/ / /_/ (__  ) ')
print ('      \\____/_/      /_/  |__/|__/_/  |_/___/\\____/ .___/____/  ')
print ('                                                /_/            ')
print ('*************************************************************************************************')
print ('*************************************************************************************************')
print ('')
print ('    🛰️  Discord Bot')
print ('')
print ('       Provided by:')
print ('        🇨🇭 Niklaus Hirt (nikh@ch.ibm.com)')
print ('')

print ('-------------------------------------------------------------------------------------------------')
print (' 🚀 Warming up')
print ('-------------------------------------------------------------------------------------------------')


# ----------------------------------------------------------------------------------------------------------------------------------------------------
# GET NAMESPACES
# ----------------------------------------------------------------------------------------------------------------------------------------------------
print('     ❓ Getting AIManager Namespace')
stream = os.popen("oc get po -A|grep aiops-orchestrator-controller |awk '{print$1}'")
aimanagerns = stream.read().strip()
print('        ✅ AIManager Namespace:       '+aimanagerns)




# ----------------------------------------------------------------------------------------------------------------------------------------------------
# DEFAULT VALUES
# ----------------------------------------------------------------------------------------------------------------------------------------------------
TOKEN='test'


# ----------------------------------------------------------------------------------------------------------------------------------------------------
# GET CONNECTIONS
# ----------------------------------------------------------------------------------------------------------------------------------------------------
global DATALAYER_ROUTE
global DATALAYER_USER
global DATALAYER_PWD
global api_url

# ----------------------------------------------------------------------------------------------------------------------------------------------------
# GET CONNECTIONS
# ----------------------------------------------------------------------------------------------------------------------------------------------------
print('     ❓ Getting Details Kafka')
stream = os.popen("oc get kafkatopics -n "+aimanagerns+"  | grep -v cp4waiopscp4waiops| grep cp4waiops-cartridge-logs-elk| awk '{print $1;}'")
KAFKA_TOPIC_LOGS = stream.read().strip()
stream = os.popen("oc get secret -n "+aimanagerns+" |grep 'aiops-kafka-secret'|awk '{print$1}'")
KAFKA_SECRET = stream.read().strip()
stream = os.popen("oc get secret "+KAFKA_SECRET+" -n "+aimanagerns+" --template={{.data.username}} | base64 --decode")
KAFKA_USER = stream.read().strip()
stream = os.popen("oc get secret "+KAFKA_SECRET+" -n "+aimanagerns+" --template={{.data.password}} | base64 --decode")
KAFKA_PWD = stream.read().strip()
stream = os.popen("oc get routes iaf-system-kafka-0 -n "+aimanagerns+" -o=jsonpath={.status.ingress[0].host}")
KAFKA_BROKER = stream.read().strip()
stream = os.popen("oc get secret -n "+aimanagerns+" kafka-secrets  -o jsonpath='{.data.ca\.crt}'| base64 -d")
KAFKA_CERT = stream.read().strip()

print('     ❓ Getting Details Datalayer')
stream = os.popen("oc get route  -n "+aimanagerns+" datalayer-api  -o jsonpath='{.status.ingress[0].host}'")
DATALAYER_ROUTE = stream.read().strip()
stream = os.popen("oc get secret -n "+aimanagerns+" aiops-ir-core-ncodl-api-secret -o jsonpath='{.data.username}' | base64 --decode")
DATALAYER_USER = stream.read().strip()
stream = os.popen("oc get secret -n "+aimanagerns+" aiops-ir-core-ncodl-api-secret -o jsonpath='{.data.password}' | base64 --decode")
DATALAYER_PWD = stream.read().strip()

print('     ❓ Getting Details Metric Endpoint')
stream = os.popen("oc get route -n "+aimanagerns+"| grep ibm-nginx-svc | awk '{print $2}'")
METRIC_ROUTE = stream.read().strip()
stream = os.popen("oc get secret -n "+aimanagerns+" admin-user-details -o jsonpath='{.data.initial_admin_password}' | base64 -d")
tmppass = stream.read().strip()
stream = os.popen('curl -k -s -X POST https://'+METRIC_ROUTE+'/icp4d-api/v1/authorize -H "Content-Type: application/json" -d "{\\\"username\\\": \\\"admin\\\",\\\"password\\\": \\\"'+tmppass+'\\\"}" | jq .token | sed "s/\\\"//g"')
METRIC_TOKEN = stream.read().strip()


stream = os.popen("oc get route  -n "+aimanagerns+" cpd  -o jsonpath='{.status.ingress[0].host}'")
CPD_ROUTE = stream.read().strip()





print ('')
print ('')
print ('')
print ('-------------------------------------------------------------------------------------------------')
print (' 🔎 Parameters')
print ('-------------------------------------------------------------------------------------------------')
print ('')
print ('    ---------------------------------------------------------------------------------------------')
print ('     🔎 Global Parameters')
print ('    ---------------------------------------------------------------------------------------------')
print ('           🔐 DEBUG:              '+DEBUG_ME)
print ('           🚀 ACTIVE:             '+ACTIVE)
print ('           🔐 Token:              '+TOKEN)
print ('')
print ('           👩‍💻 BOT NAME:           '+DISCORD_BOT_NAME)
print ('           👩‍💻 BOT PREFIX:         '+DISCORD_BOT_PREFIX)
print ('')
print ('')

print ('    ---------------------------------------------------------------------------------------------')
print ('     🔎 AI Manager Connection Parameters')
print ('    ---------------------------------------------------------------------------------------------')
print ('           🌏 Datalayer Route:    '+DATALAYER_ROUTE)
print ('           👩‍💻 Datalayer User:     '+DATALAYER_USER)
print ('           🔐 Datalayer Pwd:      '+DATALAYER_PWD)
print ('')
print ('')
print ('    ---------------------------------------------------------------------------------------------')
print ('     🔎 Simulation Parameters')
print ('    ---------------------------------------------------------------------------------------------')
print ('           INSTANCE_NAME:                  '+str(INSTANCE_NAME))
print ('           LOG_ITERATIONS:                 '+str(LOG_ITERATIONS))
print ('           LOG_TIME_FORMAT:                '+LOG_TIME_FORMAT)
print ('           LOG_TIME_STEPS:                 '+str(LOG_TIME_STEPS))
print ('           LOG_TIME_SKEW Logs:             '+str(LOG_TIME_SKEW))
print ('           LOG_TIME_ZONE Cert:             '+str(LOG_TIME_ZONE))
print ('')
print ('           EVENTS_TIME_SKEW:               '+str(EVENTS_TIME_SKEW))
print ('           DEMO_EVENTS_MEM:                '+str(len(DEMO_EVENTS_MEM)))
print ('           DEMO_EVENTS_FAN:                '+str(len(DEMO_EVENTS_FAN)))
print ('')
print ('           METRIC_TIME_SKEW:               '+str(METRIC_TIME_SKEW))
print ('           METRIC_TIME_STEP:               '+str(METRIC_TIME_STEP))
print ('           METRICS_TO_SIMULATE_MEM:        '+str(len(METRICS_TO_SIMULATE_MEM)))
print ('           METRICS_TO_SIMULATE_FAN_TEMP:   '+str(len(METRICS_TO_SIMULATE_FAN_TEMP)))
print ('           METRICS_TO_SIMULATE_FAN:        '+str(len(METRICS_TO_SIMULATE_FAN)))
print ('')
print ('')
print ('    ---------------------------------------------------------------------------------------------')
print('')
print('')

print ('    ---------------------------------------------------------------------------------------------')
print ('     🔎 Simulation Endpoints')
print ('    ---------------------------------------------------------------------------------------------')
print ('           KafkaBroker:           '+KAFKA_BROKER)
print ('           KafkaUser:             '+KAFKA_USER)
print ('           KafkaPWD:              '+KAFKA_PWD)
print ('           KafkaTopic Logs:       '+KAFKA_TOPIC_LOGS)
print ('           Kafka Cert:            '+KAFKA_CERT[:25]+'...')
print ('')   
print ('')   
print ('           Datalayer Route:       '+DATALAYER_ROUTE)
print ('           Datalayer User:        '+DATALAYER_USER)
print ('           Datalayer Pwd:         '+DATALAYER_PWD)
print ('')   
print ('           Metric Route:          '+METRIC_ROUTE)
print ('           Metric Token:          '+METRIC_TOKEN[:25]+'...')
print ('')   
print ('           Token:                 '+TOKEN)
print ('')   

print ('-------------------------------------------------------------------------------------------------')
print (' 🚀 Initializing Simulator')
print ('-------------------------------------------------------------------------------------------------')



# ------------------------------------------------------------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------------------------------------------------------------
# ACTIONS
# ------------------------------------------------------------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------------------------------------------------------------

def createIncidentMem():
    print ('    -------------------------------------------------------------------------------------------------')
    print ('     🚀 Running Simulator - Memory')
    print ('    -------------------------------------------------------------------------------------------------')


    print ('         🚀 Simulating Events')
    injectEventsMem(DATALAYER_ROUTE,DATALAYER_USER,DATALAYER_PWD)

    print ('         🚀 Simulating Metrics')
    injectMetricsMem(METRIC_ROUTE,METRIC_TOKEN)

    print ('         🚀 Simulating Logs')
    injectLogs(KAFKA_BROKER,KAFKA_USER,KAFKA_PWD,KAFKA_TOPIC_LOGS,KAFKA_CERT,LOG_TIME_FORMAT,DEMO_LOGS)
    print ('     ✅ DONE"')



def createIncidentFan():
    print ('    -------------------------------------------------------------------------------------------------')
    print ('     🚀 Running Simulator - Fan')
    print ('    -------------------------------------------------------------------------------------------------')


    print ('         🚀 Simulating Events Fan')
    injectEventsFan(DATALAYER_ROUTE,DATALAYER_USER,DATALAYER_PWD)

    print ('         🚀 Simulating Metrics Fan Temp')
    injectMetricsFanTemp(METRIC_ROUTE,METRIC_TOKEN)
    time.sleep(3)

    print ('         🚀 Simulating Logs')
    injectLogs(KAFKA_BROKER,KAFKA_USER,KAFKA_PWD,KAFKA_TOPIC_LOGS,KAFKA_CERT,LOG_TIME_FORMAT,DEMO_LOGS)
    print ('     ✅ DONE"')



def setInProgressID(story_id):
    print ('    -------------------------------------------------------------------------------------------------')
    print ('     🚀 Updating Story')
    print ('    -------------------------------------------------------------------------------------------------')

    print ('         🚀 Updating Story to "inProgress" - '+story_id)
    updateStoriesID(DATALAYER_ROUTE,DATALAYER_USER,DATALAYER_PWD,"inProgress",story_id)
    print ('     ✅ DONE"')


def setResolvedID(story_id):
    print ('    -------------------------------------------------------------------------------------------------')
    print ('     🚀 Updating Story')
    print ('    -------------------------------------------------------------------------------------------------')

    print ('         🚀 Updating Story to "resolved" - '+story_id)
    updateStoriesID(DATALAYER_ROUTE,DATALAYER_USER,DATALAYER_PWD,"resolved",story_id)
    print ('     ✅ DONE"')



def setInProgress():
    print ('    -------------------------------------------------------------------------------------------------')
    print ('     🚀 Updating Stories')
    print ('    -------------------------------------------------------------------------------------------------')

    print ('         🚀 Updating Stories to "inProgress"')
    updateStories(DATALAYER_ROUTE,DATALAYER_USER,DATALAYER_PWD,"inProgress")
    print ('     ✅ DONE"')



def setResolved():
    print ('    -------------------------------------------------------------------------------------------------')
    print ('     🚀 Updating Stories')
    print ('    -------------------------------------------------------------------------------------------------')

    print ('         🚀 Updating Stories to "resolved"')
    updateStories(DATALAYER_ROUTE,DATALAYER_USER,DATALAYER_PWD,"resolved")
    print ('     ✅ DONE"')
 

    
def setClosed():
    print ('    -------------------------------------------------------------------------------------------------')
    print ('     🚀 Updating Stories')
    print ('    -------------------------------------------------------------------------------------------------')

    print ('     🚀 Updating Stories and Alerts to "closed"')
    updateAlerts(DATALAYER_ROUTE,DATALAYER_USER,DATALAYER_PWD,"closed")
    updateStories(DATALAYER_ROUTE,DATALAYER_USER,DATALAYER_PWD,"closed")
    print ('     ✅ DONE"')





# ------------------------------------------------------------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------------------------------------------------------------
# STORY BOT
# ------------------------------------------------------------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------------------------------------------------------------

class StoryBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix=commands.when_mentioned_or('/'), intents=intents)



    # ------------------------------------------------------------------------------------------------------------------------------------------------------------
    # HANDLE MESSAGES
    # ------------------------------------------------------------------------------------------------------------------------------------------------------------
    async def on_message(self, message):
        if message.author.id == self.user.id:
            return

        if message.content.startswith(DISCORD_BOT_PREFIX+'guess'):
            await message.channel.send('Guess a number between 1 and 10.')

        if message.content.startswith(DISCORD_BOT_PREFIX+DISCORD_BOT_NAME):
            myMessage=message.content
            myArguments=myMessage.split()

            # ------------------------------------------------------------------------------------------------------------------------------------------------------------
            # EMPTY COMMAND
            if len(myArguments) < 2:
                print(" 📥 Command: EMPTY")
                await message.channel.send('**Welcome to the Watson AIOps Discord Bot for the '+INSTANCE_NAME+' Environment**')

                await message.channel.send(' You can use the following commands:')
                await message.channel.send('   🚀 Command Buttons:')
                await message.channel.send('      '+DISCORD_BOT_PREFIX+DISCORD_BOT_NAME+' **go**          :  Prints buttons to create or mitigate incidents')
                await message.channel.send('   🚀 Information:')
                await message.channel.send('      '+DISCORD_BOT_PREFIX+DISCORD_BOT_NAME+' **stories**     :  List all Stories')
                await message.channel.send('   🚀 Simulation:')
                await message.channel.send('      '+DISCORD_BOT_PREFIX+DISCORD_BOT_NAME+' **incident**    :  Simulates a Memory leak in RobotShop')
                await message.channel.send('      '+DISCORD_BOT_PREFIX+DISCORD_BOT_NAME+' **incidentMem** :  Simulates a Memory leak in RobotShop')
                await message.channel.send('      '+DISCORD_BOT_PREFIX+DISCORD_BOT_NAME+' **incidentFan** :  Simulates a Fan problem in RobotShop')
                await message.channel.send('   🚀 Modify Stories:')
                await message.channel.send('      '+DISCORD_BOT_PREFIX+DISCORD_BOT_NAME+' **progress**    :  Set all Stories to InProgress')
                await message.channel.send('      '+DISCORD_BOT_PREFIX+DISCORD_BOT_NAME+' **resolve **    :  Set all Stories to Resolved')
                await message.channel.send('      '+DISCORD_BOT_PREFIX+DISCORD_BOT_NAME+' **close**       :  Set all Stories to Resolved')
                await message.channel.send('      '+DISCORD_BOT_PREFIX+DISCORD_BOT_NAME+' **reset**       :  Set all Stories to Resolved')
            else:
                myArgument=myArguments[1]


                # ------------------------------------------------------------------------------------------------------------------------------------------------------------
                # BOT COMMANDS
                # ------------------------------------------------------------------------------------------------------------------------------------------------------------
                 # COMMAND BUTTONS
                if myArgument == "go":
                    print(" 📥 Command: go")
                    await message.channel.send('🚀 '+INSTANCE_NAME+' Quick Commands')

                    view = StoriesActions()
                    await message.channel.send(view=view)

                    view = IncidentActions()
                    await message.channel.send(view=view)
                    await message.channel.send(' \ntype "'+DISCORD_BOT_PREFIX+DISCORD_BOT_NAME+' help" to get a list of all possible commands.')

                
                
                # CREATE INCIDENT MEMORY LEAK
                elif myArgument == "incident":
                    print(" 📥 Command: incident")
                    await message.channel.send('🚀 '+INSTANCE_NAME+' Simulating Memory Incident')
                    print('    🟠 Create THREADS')
                    threadRun = Thread(target=createIncidentMem)
                    print('    🟠 Start THREADS')
                    threadRun.start()
                    await message.channel.send('✅ Simulation is running in the background')


                # ------------------------------------------------------------------------------------------------------------------------------------------------------------
                # CREATE INCIDENT MEMORY LEAK
                elif myArgument == "incidentMem":
                    print(" 📥 Command: incidentMem")
                    await message.channel.send('🚀 '+INSTANCE_NAME+' Simulating Memory Incident')
                    print('    🟠 Create THREADS')
                    threadRun = Thread(target=createIncidentMem)
                    print('    🟠 Start THREADS')
                    threadRun.start()
                    await message.channel.send('✅ Simulation is running in the background')


                # ------------------------------------------------------------------------------------------------------------------------------------------------------------
                # CREATE INCIDENT FAN FAILURE
                elif myArgument == "incidentFan":
                    print(" 📥 Command: incidentFan")
                    await message.channel.send('🚀 '+INSTANCE_NAME+' Simulating Fan Incident')
                    print('    🟠 Create THREADS')
                    threadRun = Thread(target=createIncidentFan)
                    print('    🟠 Start THREADS')
                    threadRun.start()
                    await message.channel.send('✅ Simulation is running in the background')


                # ------------------------------------------------------------------------------------------------------------------------------------------------------------
                 # SET STORIES TO InProgress
                elif myArgument == "progress":
                    print(" 📥 Command: progress")
                    await message.channel.send('🚀 '+INSTANCE_NAME+' Set Stories to InProgress')
                    print('    🟠 Create THREADS')
                    threadRun = Thread(target=setInProgress)
                    print('    🟠 Start THREADS')
                    threadRun.start()


                # ------------------------------------------------------------------------------------------------------------------------------------------------------------
                 # SET STORIES TO Resolved
                elif myArgument == "resolve":
                    print(" 📥 Command: resolve")
                    await message.channel.send('🚀 '+INSTANCE_NAME+' Set Stories to Resolved')
                    print('    🟠 Create THREADS')
                    threadRun = Thread(target=setResolved)
                    print('    🟠 Start THREADS')
                    threadRun.start()

                # ------------------------------------------------------------------------------------------------------------------------------------------------------------
                 # SET STORIES TO Resolved
                elif myArgument == "close":
                    print(" 📥 Command: close")
                    await message.channel.send('🚀 '+INSTANCE_NAME+' Set Stories to Resolved')
                    print('    🟠 Create THREADS')
                    threadRun = Thread(target=setResolved)
                    print('    🟠 Start THREADS')
                    threadRun.start()


                # ------------------------------------------------------------------------------------------------------------------------------------------------------------
                 # SET STORIES TO Resolved
                elif myArgument == "reset":
                    print(" 📥 Command: reset")
                    await message.channel.send('🚀 '+INSTANCE_NAME+' Reset Demo Environment')
                    print('    🟠 Create THREADS')
                    threadRun = Thread(target=setResolved)
                    print('    🟠 Start THREADS')
                    threadRun.start()
                    await message.channel.send('ℹ️ Give the environment 5 Minutes to clean up')


                # ------------------------------------------------------------------------------------------------------------------------------------------------------------
                # WELCOME MESSAGE
                elif (myArgument == "welcome") or (myArgument == "help"):
                    print(" 📥 Command: "+myArgument)
                    await message.channel.send('**Welcome to the Watson AIOps Discord Bot for the '+INSTANCE_NAME+' Environment**')

                    await message.channel.send(' You can use the following commands:')
                    await message.channel.send('   🚀 Command Buttons:')
                    await message.channel.send('      '+DISCORD_BOT_PREFIX+DISCORD_BOT_NAME+' **go**          :  Prints buttons to create or mitigate incidents')
                    await message.channel.send('   🚀 Simulation:')
                    await message.channel.send('      '+DISCORD_BOT_PREFIX+DISCORD_BOT_NAME+' **incident**    :  Simulates a Memory leak in RobotShop')
                    await message.channel.send('      '+DISCORD_BOT_PREFIX+DISCORD_BOT_NAME+' **incidentMem** :  Simulates a Memory leak in RobotShop')
                    await message.channel.send('      '+DISCORD_BOT_PREFIX+DISCORD_BOT_NAME+' **incidentFan** :  Simulates a Fan problem in RobotShop')
                    await message.channel.send('   🚀 Information:')
                    await message.channel.send('      '+DISCORD_BOT_PREFIX+DISCORD_BOT_NAME+' **stories**     :  List all Stories')
                    await message.channel.send('   🚀 Modify Stories:')
                    await message.channel.send('      '+DISCORD_BOT_PREFIX+DISCORD_BOT_NAME+' **progress**    :  Set all Stories to InProgress')
                    await message.channel.send('      '+DISCORD_BOT_PREFIX+DISCORD_BOT_NAME+' **resolve **    :  Set all Stories to Resolved')
                    await message.channel.send('      '+DISCORD_BOT_PREFIX+DISCORD_BOT_NAME+' **close**       :  Set all Stories to Resolved')
                    await message.channel.send('      '+DISCORD_BOT_PREFIX+DISCORD_BOT_NAME+' **reset**       :  Set all Stories to Resolved')




                # ------------------------------------------------------------------------------------------------------------------------------------------------------------
                # GET STORIES
                elif myArgument == "stories":
                    print(" 📥 Command: stories")
                    await message.channel.send('**🚀 '+INSTANCE_NAME+' Open Stories**')
                    await message.channel.send('-------------------------------------------------------------------')
                    actStories=getStories(DATALAYER_ROUTE,DATALAYER_USER,DATALAYER_PWD, CPD_ROUTE)
                    for currentStory in actStories['stories']:
                        outputString=""
                        story_id=currentStory["id"]
                        storyState=currentStory["state"]
                        if storyState=="assignedToIndividual":
                            stateString="🔵 Assigned To Individual"
                        elif storyState=="inProgress":
                            stateString="🟢 In Progress"
                        elif storyState=="onHold":
                            stateString="🟠 On Hold"
                        elif storyState=="resolved":
                            stateString="🔴 Resolved"
                        elif storyState=="closed":
                            stateString="❌ Closed"
                        else:
                            stateString=state
                        title=currentStory["title"]
                        priority=currentStory["priority"]
                        owner=currentStory["owner"]
                        url='https://'+CPD_ROUTE+'/aiops/cfd95b7e-3bc7-4006-a4a8-a73a79c71255/resolution-hub/stories/all/'+story_id+'/overview'
                        #debug(currentStory)
                        # print('     ✅ Name: '+title)
                        # print('     ✅ priority: '+str(priority))
                        # print('     ✅ owner: '+owner)

                        outputString=outputString+'\n\n🚀 **'+title.strip()+'**\n   > Priority: '+str(priority)+'\n   > Owner: '+owner+'\n   > State: '+stateString+'\n\n' 
                        # print('     ✅ Story: '+outputString)
                        # print('      ')
                        await message.channel.send(outputString)

                        # We create the view and assign it to a variable so we can wait for it later.
                        view = Story(story_id,url)
                        await message.channel.send(view=view)

                        view = StoryActions(story_id,url)
                        await message.channel.send(view=view)
                        await message.channel.send('-------------------------------------------------------------------')


                    await message.channel.send('✅ DONE')





                # ------------------------------------------------------------------------------------------------------------------------------------------------------------
                # UNKNOWN COMMAND
                else:
                    print(" ❗Unknown Command")
                    await message.channel.send('🟠 Unknown Command '+myArgument+'. Type "'+DISCORD_BOT_PREFIX+DISCORD_BOT_NAME+' welcome" to get a list of available commands.')




    # ------------------------------------------------------------------------------------------------------------------------------------------------------------
    # HANDLE REACTIONS
    # ------------------------------------------------------------------------------------------------------------------------------------------------------------
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """Gives a role based on a reaction emoji."""
        # Make sure that the message the user is reacting to is the one we care about.
        print('A:'+str(payload))
        print('B:'+str(self.fetch_user))






# ------------------------------------------------------------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------------------------------------------------------------
# CUSTOM VIEWS
# ------------------------------------------------------------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------------------------------------------------------------
class Story(discord.ui.View):
    def __init__(self, storyID: str, storyURL: str):
        super().__init__()
        # print ("storyID"+storyID)
        # print ("storyURL"+storyURL)

        self.add_item(discord.ui.Button(label='Open Story: ', style=discord.ButtonStyle.green, url=storyURL))


class StoryActions(discord.ui.View):
    def __init__(self, storyID: str, storyURL: str):
        super().__init__(timeout=None)
        self.currentStoryID=storyID
        self.add_buttons(self.currentStoryID)

    def add_buttons(self,currentStoryID):
            button_green = discord.ui.Button(label='Acknowledge Story', style=discord.ButtonStyle.green)
            button_red = discord.ui.Button(label='Resolve Story', style=discord.ButtonStyle.red)

            async def fbutton_green(interaction: discord.Interaction):
                await interaction.response.send_message('🟠 Acknowledge Story', ephemeral=True)
                print('AWAIT'+currentStoryID)
                setInProgressID(currentStoryID)

            async def fbutton_red(interaction: discord.Interaction):
                print(self.currentStoryID)
                await interaction.response.send_message('🔴 Resolve Story', ephemeral=True)
                print('AWAIT'+currentStoryID)
                setResolvedID(currentStoryID)

            button_green.callback = fbutton_green
            self.add_item(button_green)
            button_red.callback = fbutton_red
            self.add_item(button_red)


class StoriesActions(discord.ui.View):
    def __init__(self):
        super().__init__()

    @discord.ui.button(label='Acknowledge all Stories', style=discord.ButtonStyle.green, custom_id='persistent_view:ackall')
    async def green(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message('🟠 Acknowledged all Stories', ephemeral=True)
        setInProgress()

    @discord.ui.button(label='Resolve all Stories', style=discord.ButtonStyle.green, custom_id='persistent_view:closeall')
    async def red(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message('🔴 Resolved all Stories', ephemeral=True)
        setResolved()


class IncidentActions(discord.ui.View):
    def __init__(self):
        super().__init__()

    @discord.ui.button(label='Create Incident - Memory Leak', style=discord.ButtonStyle.red, custom_id='persistent_view:mem')
    async def green(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message('🚀 Simulating Memory Incident', ephemeral=True)
        print('    🟠 Create THREADS')
        threadRun = Thread(target=createIncidentMem)
        print('    🟠 Start THREADS')
        threadRun.start()


    @discord.ui.button(label='Create Incident - Fan Failure', style=discord.ButtonStyle.red, custom_id='persistent_view:fan')
    async def red(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message('🚀 Simulating Fan Incident', ephemeral=True)
        print('    🟠 Create THREADS')
        threadRun = Thread(target=createIncidentFan)
        print('    🟠 Start THREADS')
        threadRun.start()



# ------------------------------------------------------------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------------------------------------------------------------
# RUN THIS PUPPY
# ------------------------------------------------------------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------------------------------------------------------------
bot = StoryBot()


if ACTIVE=="True": 
    if DISCORD_BOT_TOKEN=="CHANGEME": 
        print ('-------------------------------------------------------------------------------------------------')
        print (' ❗ Bot Token not defined!!!')
        print ('-------------------------------------------------------------------------------------------------')
    else:
        bot.run(DISCORD_BOT_TOKEN)
else:
    while True:
        print ('-------------------------------------------------------------------------------------------------')
        print (' ❗ Bot is DISABLED')
        print ('-------------------------------------------------------------------------------------------------')
        time.sleep(15)


print ('')
print ('')
print ('')
print ('-------------------------------------------------------------------------------------------------')
print (' ✅ Bot is DONE')
print ('-------------------------------------------------------------------------------------------------')
print ('')
print ('')





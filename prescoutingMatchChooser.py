import json, datetime, http.client
# HTTP Connection is global so it only has to be made once at the start
tbaConn = http.client.HTTPConnection("www.thebluealliance.com")
# Read auth key from tbaAuth.txt, which should be in the same directory as this file
tbaAuth = open("tbaAuth.txt", "r").read()

# Make a TBA request, returns json object
def tbaRequest(query):
    global tbaConn, tbaAuth
    # Send "GET" HTTP request
    tbaConn.request("GET", "/api/v3/" + query + "?X-TBA-Auth-Key=" + tbaAuth)
    # Read request and convert to json object
    return json.loads(tbaConn.getresponse().read())

# If event is in the future, or if event type is undefined, offseason, or preseason, return that it is not suitable for scouting
isScoutable = lambda eventType, eventDate: not (eventType < 0 or eventType > 5 or eventDate > datetime.date.today())

# Makes sure that the event key entered is valid
eventKeyInvalid = True
while(eventKeyInvalid):
    eventKeyInvalid = False
    # Input event key
    eventKey = input("Enter event key: ")
    # Make a list teamKeys with all teams attending the specified event
    eventTeamsReq = tbaRequest("event/" + eventKey + "/teams")
    teamKeys = []
    # If event key is invalid, print error message and re-enter event key
    try:
        for e in eventTeamsReq:
            teamKeys.append(e["key"])
    except:
        eventKeyInvalid = True
        print("[ERROR]: This event doesn't exist. Try again.")

# Input how many matches to prescout per team (can only be 2 or 4)
numToScoutInvalid = True
while(numToScoutInvalid):
    numToScoutInvalid = False
    try:
        numToScout = int(input("How many matches to prescout per team? (2 or 4): "))
        if(not(numToScout == 2 or numToScout == 4)):
            numToScoutInvalid = True
    except:
        numToScoutInvalid = True
    if(numToScoutInvalid):
        print("[ERROR]: Matches to scout must be either 2 or 4. Try again.")

# Initialize eventsToScout variable, which holds the team number and event key of latest scoutable event
eventsToScout = {}
# For each team, add its latest scoutable event to eventsToScout
for t in teamKeys:
    # Print status message
    print("[STATUS]: Finding latest scoutable event for " + t)
    # Request containing all events for that team in that year
    teamEventsReq = tbaRequest("team/" + t + "/events/" + eventKey[:4] + "/simple")
    # Initialize latestEvent variable, which holds event key and start date
    latestEvent = {"key": "", "date": datetime.date(1, 1, 1)}
    # Loop through each event to find the latest scoutable event
    for e in teamEventsReq:
        # Retrieves start date as string
        dateString = e["start_date"]
        # Stores event as dict, which holds event key and start date (as datetime.date object)
        currentEvent = {"key": e["key"], "date": datetime.date(int(dateString[:4]), int(dateString[5:7]), int(dateString[8:10]))}
        # If currentEvent occurs after latestEvent and is suitable for scouting, update latestEvent to currentEvent
        if(currentEvent["date"] > latestEvent["date"] and isScoutable(e["event_type"], currentEvent["date"])):
            latestEvent = currentEvent
    # Add their latest scoutable event to eventsToScout
    eventsToScout[t] = latestEvent["key"]

# Initialize matchesToScout variable, which will hold the result
matchesToScout = {}
# Loop through each team to choose which matches to scout
for t, e in eventsToScout.items():
    print("[STATUS]: Choosing matches for " + t)
    # Get a list of their matches from TBA
    matchList = tbaRequest("team/" + t + "/event/" + e + "/matches/keys")
    allMatches = {"qm": {}, "qf": {}, "sf": {}, "f": {}}
    for m in matchList:
        for i, c in enumerate(m):
            if(c == "_"):
                matchID = m[i+1:]
                break
        if(matchID[0:2] == "qm"):
            allMatches["qm"][int(matchID[2:])] = m
        elif(matchID[0:2] == "qf"):
            allMatches["qf"][10*int(matchID[2]) + int(matchID[4:])] = m
        elif(matchID[0:2] == "sf"):
            allMatches["sf"][10*int(matchID[2]) + int(matchID[4:])] = m
        elif(matchID[0:2] == "f"):
            allMatches["f"][10*int(matchID[1]) + int(matchID[3:])] = m
    sortedQM = sorted(allMatches["qm"])
    sortedQF = sorted(allMatches["qf"])
    sortedSF = sorted(allMatches["sf"])
    sortedF = sorted(allMatches["f"])
    matchesToScout[t] = []
    if(numToScout == 2):
        playoffsChosen = False
        try:
            matchesToScout[t].append(allMatches["f"][sortedF.pop()])
        except:
            True
        if(len(matchesToScout[t]) < 1):
            try:
                matchesToScout[t].append(allMatches["sf"][sortedSF.pop()])
            except:
                True
        if(len(matchesToScout[t]) < 1):
            try:
                matchesToScout[t].append(allMatches["qf"][sortedQF.pop()])
            except:
                True
        while(len(matchesToScout[t]) < 2 and len(sortedQM) > 0):
            matchesToScout[t].append(allMatches["qm"][sortedQM.pop()])
    else:
        try:
            matchesToScout[t].append(allMatches["f"][sortedF.pop()])
        except:
            True
        try:
            matchesToScout[t].append(allMatches["sf"][sortedSF.pop()])
        except:
            True
        while(len(matchesToScout[t]) < 2 and len(sortedQF) > 0):
            matchesToScout[t].append(allMatches["qf"][sortedQF.pop()])
        while(len(matchesToScout[t]) < 4 and len(sortedQM) > 0):
            matchesToScout[t].append(allMatches["qm"][sortedQM.pop()])
print(matchesToScout)

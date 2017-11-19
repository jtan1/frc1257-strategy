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
matchesToScoutInvalid = True
while(matchesToScoutInvalid):
    matchesToScoutInvalid = False
    try:
        matchesToScout = int(input("How many matches to prescout per team? (2 or 4): "))
        if(not(matchesToScout == 2 or matchesToScout == 4)):
            matchesToScoutInvalid = True
    except:
        matchesToScoutInvalid = True
    if(matchesToScoutInvalid):
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
    # Initialize allMatches variable, which will use a unique integer to identify each match (the later a match was played, the larger its integer)
    allMatches = {}
    # Loop through each match key returned by the TBA request
    for m in matchList:
        # Set MatchID to everything in the match key after the underscore (removing the event info)
        for i, c in enumerate(m):
            if(c == "_"):
                matchID = m[i+1:]
                break
        # If match is in quals, its representative integer is less than 200 (it's just the number of the qual)
        if(matchID[0:2] == "qm"):
            allMatches[int(matchID[2:])] = m
        # If match is in quarters, its representative integer is between 200 and 300
        elif(matchID[0:2] == "qf"):
            allMatches[200 + 10*int(matchID[2]) + int(matchID[4:])] = m
        # If match is in semis, its representative integer is between 300 and 400
        elif(matchID[0:2] == "sf"):
            allMatches[300 + 10*int(matchID[2]) + int(matchID[4:])] = m
        # If match is in finals, its representative integer is between 400 and 500
        elif(matchID[0:2] == "f"):
            allMatches[400 + 10*int(matchID[1]) + int(matchID[3:])] = m
    # Sort matches in reverse chronological order
    sortedMatches = sorted(allMatches, reverse=True)
    # Initialize matchesChosen variable
    matchesChosen = []
    # If scouting 2 matches per team, choose one playoff (if available) and the rest quals
    if(matchesToScout == 2):
        # Loop through matches in reverse chronological order
        for n in sortedMatches:
            # If match is from playoffs and a playoffs match has not already been chosen, then choose it
            if(n > 200):
                if(len(matchesChosen) == 0):
                    matchesChosen.append(n)
            # Keep choosing quals until two matches have been chosen
            else:
                if(len(matchesChosen) < 2):
                    matchesChosen.append(n)
    # If scouting 4 matches per team, choose two playoffs (from different levels if possible) and the rest quals
    else:
        # Initialize temporary variables finalsChosen and semisChosen
        finalsChosen = False
        semisChosen = False
        # Loop through matches in reverse chronological order
        for n in sortedMatches:
            # If match is from finals and a finals match has not already been chosen, then choose it
            if(n > 400):
                if(not finalsChosen):
                    matchesChosen.append(n)
                    finalsChosen = True
            # If match is from semis and a semis match has not already been chosen, then choose it
            elif(n > 300):
                if(not semisChosen):
                    matchesChosen.append(n)
                    semisChosen = True
            # Keep choosing quarters until two playoffs matches have been chosen
            elif(n > 200):
                if(len(matchesChosen) < 2):
                    matchesChosen.append(n)
            # Keep choosing quals until four matches have been chosen
            else:
                if(len(matchesChosen) < 4):
                    matchesChosen.append(n)
    # For each team, initialize a dict entry in matchesToScout to hold the chosen matches
    matchesToScout[t] = []
    # Loop through each match chosen and add its match key to matchesToScout[t]
    for n in matchesChosen:
        matchesToScout[t].append(allMatches[n])
print(matchesToScout)

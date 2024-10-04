import glob
import pandas as pd
import numpy as np
import math

'''
Notes:
Must include file with entries in the tournament folder, then two folders
with all of the prelims and elims in order
'''

def entry_dict(tournament):
    '''make a dictionary with all of the entries at a tournament with school and names'''
    outputDict = {}
    
    file_location = glob.glob("Documents/Debate/SideBias/" + tournament + "/*.csv")[0]
    if not file_location:
        raise FileNotFoundError(f"No CSV file found in folder:" + str(file_location))
    
    teams = pd.read_csv(file_location, delimiter=",", header=0, usecols=[2, 3])
    teams = teams.to_numpy()
    
    for team in teams:
        school, name = team[1], team[0]
        if name == "Michael Meng":
            if "Lawrenceville" in school:
                name = "Michael Meng (Lawrenceville)"
            else:
                name = "Michael Meng (Strake)"
        outputDict[school] = [name, school]
    
    print("Processed entries for " + tournament)    
    
    return outputDict

bidList = {}
K = 30

rounds = 0
elims = 0
negWs = 0
elimNegWs = 0

elos_dict = {}

def glickoPrelims(tournament, teamsDict, elos_dict, bid):
    # Adds tournament prelims based off the glicko ranking system WITHOUT volatility calculations
    
    global rounds, elims, negWs, elimNegWs
    
    files = glob.glob("Documents/Debate/SideBias/" + tournament + "/Prelims/*.csv")
    if len(files) == 0:
        raise Exception("Error in reading prelims from {}.".format(tournament))
    
    for file in files:
        file = open(file, "r", encoding="Latin-1")
        
        for line in file.readlines()[1:]:
            line = line.split(",")
            team1, team2, judge, result = tuple(line[0:4])
            
            result = result.lower()
            
            if "bye" in result or "bye" in team1 or "bye" in team2 or "bye" in judge or judge == "" or "fft" in result:
                continue
            
            rounds += 1
            
            if "neg" in result or "con" in result:
                team1, team2 = team2, team1  # team 1 is the winning team
                negWs += 1
                
            try:
                team1, team2 = teamsDict[team1], teamsDict[team2]  # this line for no school names
                '''team1, team2 = team1[:-3] + " " + teamsDict[team1], team2[:-3] + " " + teamsDict[team2]'''  # this line for school names (buggy)
            except:
                continue
            
            try:
                elo_team1 = elos_dict[team1[0]][0]
                rd_team1 = elos_dict[team1[0]][2]

            except:
                elo_team1 = 1500
                rd_team1 = 350

            
            try:
                elo_team2 = elos_dict[team2[0]][0]
                rd_team2 = elos_dict[team2[0]][2]

            except:
                elo_team2 = 1500
                rd_team2 = 350

            
            mu1 = (elo_team1 - 1500)/173.7178
            sig1 = (rd_team1)/173.7178
            
            mu2 = (elo_team2-1500)/173.7178
            sig2 = rd_team2/173.7178
            
            # player 1 calcs
            gsig1 = 1/(math.sqrt(1 + (3*(sig2**2)/(math.pi**2))))
            ef1 = 1/(1 + pow(math.e, (-gsig1 * (mu1 - mu2))))
            v1 = 1/((gsig1**2)*ef1*(1-ef1))
            d1 = gsig1 * (1 - ef1) # should be 0 -ef1 for a loss
            # glicko would update player volatility here. I'm keeping it constant at .06.
            
            sig1 = math.sqrt(sig1**2 + math.pow(0.06,2))
            sig1 = 1/math.sqrt((1/sig1) + (1/v1))
            mu1 = mu1 + (sig1**2 * d1)
            
            # player 2 calcs
            gsig2 = 1/math.sqrt(1 + (3*(sig1**2)/(math.pi**2)))
            ef2 = 1/(1 + pow(math.e, (-gsig2 * (mu2 - mu1))))
            v2 = 1/((gsig2**2)*ef2*(1-ef2))
            d2 = gsig2 * (0 - ef2) # should be 0 -ef1 for a loss
            # glicko would update player volatility here. I'm keeping it constant at .06.
            
            sig2 = math.sqrt(sig2**2 + math.pow(0.06,2))
            sig2 = 1/math.sqrt((1/sig2) + (1/v2))
            mu2 = mu2 + (sig2**2 * d2)
            
            # updating ELOs
            eloDelta1 = 173.7178 * mu1 
            eloDelta2 = 173.7178 * mu2 
            
            elo_team1 = eloDelta1 + 1500
            rd_team1 = 173.7178 * sig1
            
            elo_team2 = eloDelta2 + 1500
            rd_team2 = 173.7178 * sig2
            
            elos_dict[team1[0]] = [elo_team1,team1[1], rd_team1]
            elos_dict[team2[0]] = [elo_team2,team2[1], rd_team2]
        file.close()
    return elos_dict
    
def glickoElims(tournament, teamsDict, elos_dict, bid):
    '''adds the elims of a tournament to the rankings'''
    
    global rounds, elims, negWs, elimNegWs
    
    files = glob.glob("Documents/Debate/SideBias/" + tournament + "/Elims/*.csv")
    if len(files) == 0:
        raise Exception("Error in reading elims from {}".format(tournament))
    
    for file in files:
        file = open(file, "r", encoding="Latin-1")
        lines = file.readlines()[1:]
        
        for line in lines:
            isBid = False
            
            if len(lines) == bid:
                isBid = True
            line = line.split(",")
            
            try:
                team1, team2, judge, votes, result = tuple(line[0:5])
            except:
                continue
            
            result = result.lower()
            
            try:
                margin, result = tuple(result[1:-2].split())
            except:
                continue
            
            if "bye" in result or "BYE" in team1 or "BYE" in team2 or "BYE" in judge or "bye" in margin:
                continue

            rounds += 1
            elims += 1
            
            if "neg" in result or "con" in result:
                team1, team2 = team2, team1  # team 1 is the winning team
                negWs += 1
                elimNegWs += 1

            team1, team2 = teamsDict[team1], teamsDict[team2] #this line for no school names

            '''team1, team2 = team1[:-3] + " " + teamsDict[team1], team2[:-3] + " " + teamsDict[team2]''' #this line for school names (buggy)

            if isBid:
                try:
                    bidList[team1[0]] += 1
                except:
                    bidList[team1[0]] = 1
                try:
                    bidList[team2[0]] += 1
                except:
                    bidList[team2[0]] = 1

            try:
                elo_team1 = elos_dict[team1[0]][0]
                rd_team1 = elos_dict[team1[0]][2]

            except:
                elo_team1 = 1500
                rd_team1 = 350

            
            try:
                elo_team2 = elos_dict[team2[0]][0]
                rd_team2 = elos_dict[team2[0]][2]

            except:
                elo_team2 = 1500
                rd_team2 = 350

            
            mu1 = (elo_team1 - 1500)/173.7178
            sig1 = (rd_team1)/173.7178
            
            mu2 = (elo_team2-1500)/173.7178
            sig2 = rd_team2/173.7178
            
            # player 1 calcs
            gsig1 = 1/(math.sqrt(1 + (3*(sig2**2)/(math.pi**2))))
            ef1 = 1/(1 + pow(math.e, (-gsig1 * (mu1 - mu2))))
            v1 = 1/((gsig1**2)*ef1*(1-ef1))
            d1 = gsig1 * (1 - ef1) # should be 0 -ef1 for a loss
            # glicko would update player volatility here. I'm keeping it constant at .06.
            
            sig1 = math.sqrt(sig1**2 + math.pow(0.06,2))
            sig1 = 1/math.sqrt((1/sig1) + (1/v1))
            mu1 = mu1 + (sig1**2 * d1)
            
            # player 2 calcs
            gsig2 = 1/math.sqrt(1 + (3*(sig1**2)/(math.pi**2)))
            ef2 = 1/(1 + pow(math.e, (-gsig2 * (mu2 - mu1))))
            v2 = 1/((gsig2**2)*ef2*(1-ef2))
            d2 = gsig2 * (0 - ef2) # should be 0 -ef1 for a loss
            # glicko would update player volatility here. I'm keeping it constant at .06.
            
            sig2 = math.sqrt(sig2**2 + math.pow(0.06,2))
            sig2 = 1/math.sqrt((1/sig2) + (1/v2))
            mu2 = mu2 + (sig2**2 * d2)
            
            # updating ELOs
            eloDelta1 = 173.7178 * mu1 
            eloDelta2 = 173.7178 * mu2 
            
            elo_team1 = eloDelta1 + 1500
            rd_team1 = 173.7178 * sig1
            
            elo_team2 = eloDelta2 + 1500
            rd_team2 = 173.7178 * sig2
            
            elos_dict[team1[0]] = [elo_team1,team1[1], rd_team1]
            elos_dict[team2[0]] = [elo_team2,team2[1], rd_team2]
        file.close()
    return elos_dict

bParam = 0

def eloAdjustedWinElims(tournament, teamsDict, elos_dict, bid): # will work on later.
    
    global bParam
    
    files = glob.glob("Documents/Debate/SideBias/" + tournament + "/Elims/*.csv")
    if len(files) == 0:
        raise Exception("Error in reading elims from {}".format(tournament))
    
    for file in files:
        file = open(file, "r", encoding="Latin-1")
        lines = file.readlines()[1:]
        
        for line in lines:
            line = line.split(",")
            try:
                team1, team2, judge, votes, result = tuple(line[0:5])
            except:
                continue
            
            result = result.lower()
            
            try:
                margin, result = tuple(result[1:-2].split())
            except:
                continue
            
            if "bye" in result or "BYE" in team1 or "BYE" in team2 or "BYE" in judge or "bye" in margin:
                continue
            
            team1, team2 = teamsDict[team1], teamsDict[team2] #this line for no school names

            elo_team1 = elos_dict[team1[0]][0]
            
            elo_team2 = elos_dict[team2[0]][0]
            
            incidentB = np.log(-0.8)
            
            
            
        file.close()
    return elos_dict


def add_tournament(tournament, bid):
    '''adds a tournament to the rankings'''
    dictionary = entry_dict(tournament)
    glickoPrelims(tournament, dictionary, elos_dict, bid)
    glickoElims(tournament, dictionary, elos_dict, bid)


def write_to_csv(elosList):
    '''write the rankings to the csv'''
    add = "Rank,School,Name,Elo\n"
    counter = 0
    for team, eloSchool in elosList:
        elo, school = eloSchool[0], eloSchool[1]
        counter += 1
        name = " ".join(team.split())
        
        add += str(counter) + "," + school + "," + name + "," + str(round(elo*1000)/1000) + "\n"
        
    with open("Documents/Debate/SideBias/LDRankings.csv", "w") as fp:
        fp.write(add[:-1])
        

add_tournament("Loyola", 4)
add_tournament("SeasonOpener", 4)
add_tournament("Grapevine", 4)
add_tournament("Yale", 4)
add_tournament("MidAmericaCup", 8)
add_tournament("JackHowe", 2)
add_tournament("Greenhill", 8)

negPercent = negWs/rounds
negElimPercent = elimNegWs/elims
print("Neg wins " +  str(negPercent) + ". Rounds: "+ str(negWs) + "/" + str(rounds))
print("Elim Neg wins " +  str(negElimPercent) + ". Rounds: " + str(elimNegWs) + "/" + str(elims))

elos = sorted(elos_dict.items(), key=lambda item: item[1], reverse=True)
write_to_csv(elos)
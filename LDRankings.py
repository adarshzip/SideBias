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
    '''make a dictionary with all of the entries at a  with school and names'''
    outputDict = {}
    file_location = glob.glob("Documents/Debate/SideBias/" + tournament + "/*.csv")[0]
    if not file_location:
        raise FileNotFoundError(f"No CSV file found in folder:" + str(file_location))
    
    teams = pd.read_csv(file_location, delimiter=",", header=0, usecols=[2, 3])
    teams = teams.to_numpy()
    for team in teams:
        if team[1] == 'Archbishop Mitty AP':
            team[0] = 'Andrew Park (Mitty)'
        if (team[1] == 'Troy Independent AP') or (team[1] == 'Troy AP'):
            team[0] = 'Andrew Park (Troy)'
        print(team)
        school, name = team[1], team[0]
        outputDict[school] = [name, school]
    return outputDict

bidList = {}
K = 30

rounds = 0
elims = 0
negWs = 0
elimNegWs = 0

def add_prelims(tournament, teamsDict, elos_dict, bid):
    '''adds the prelims of a tournament to the rankings'''
    global rounds, elims, negWs, elimNegWs
    files = glob.glob("Documents/Debate/SideBias/" + tournament + "/Prelims/*.csv")
    if len(files) == 0:
        raise Exception("Error in reading prelims from {}.".format(tournament))
    for file in files:
        file = open(file, "r", encoding="Latin-1")
        for line in file.readlines()[1:]:
            line = line.split(",")
            team1, team2, judge, result = tuple(line[0:4])
            rounds += 1
            result = result.lower()
            if "bye" in result or "BYE" in team1 or "BYE" in team2 or "BYE" in judge:
                rounds -= 1
                continue
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
            except:
                elo_team1 = 1500
            try:
                elo_team2 = elos_dict[team2[0]][0]
            except:
                elo_team2 = 1500
            elo_diff = elo_team1 - elo_team2
            winProb = 1.0 / (math.pow(10.0, (-elo_diff / 400.0)) + 1.0)
            shift = K * (1 - winProb) * ((bid / 8) ** .5)
            elo_team1 += shift
            elo_team2 -= shift
            elos_dict[team1[0]] = [elo_team1,team1[1]]
            elos_dict[team2[0]] = [elo_team2,team2[1]]
        file.close()
    return elos_dict


elos_dict = {}


def add_elims(tournament, teamsDict, elos_dict, bid):
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

            try:
                elo_team1 = elos_dict[team1[0]][0]
            except:
                elo_team1 = 1500
            try:
                elo_team2 = elos_dict[team2[0]][0]
            except:
                elo_team2 = 1500
            if isBid:
                try:
                    bidList[team1[0]] += 1
                except:
                    bidList[team1[0]] = 1
                try:
                    bidList[team2[0]] += 1
                except:
                    bidList[team2[0]] = 1
            elo_diff = elo_team1 - elo_team2
            winProb = 1.0 / (math.pow(10.0, (-elo_diff / 400.0)) + 1.0)
            shift = K * (1 - winProb) * ((bid / 8) ** .5)
            try:
                [bw, bl] = margin.split("-")
                shift *= (1 + (int(bw) - 1) / (int(bl) + 1))
            except:
                continue
            elo_team1 += shift + bid
            elo_team2 -= shift / 2
            elos_dict[team1[0]] = [elo_team1,team1[1]]
            elos_dict[team2[0]] = [elo_team2,team2[1]]
        file.close()
    return elos_dict


def add_tournament(tournament, bid):
    '''adds a tournament to the rankings'''
    dictionary = entry_dict(tournament)
    add_prelims(tournament, dictionary, elos_dict, bid)
    add_elims(tournament, dictionary, elos_dict, bid)


def write_to_csv(elosList):
    '''write the rankings to the csv'''
    add = "Rank,School,Name,Elo,Bids,\n"
    counter = 0
    for team, eloSchool in elosList:
        elo, school = eloSchool[0], eloSchool[1]
        counter += 1
        name = " ".join(team.split())
        if name in bidList:
            bids = bidList[name]
        else:
            bids = 0
        
        add += str(counter) + "," + school + "," + name + "," + str(round(elo*1000)/1000) + ",{}, \n".format(bids)
        
    with open("LDRankings.csv", "w") as fp:
        fp.write(add[:-1])


add_tournament("Loyola", 4)
add_tournament("SeasonOpener", 4)
add_tournament("Grapevine", 4)
add_tournament("Yale", 2)
add_tournament("MidAmericaCup", 8)
add_tournament("JackHowe", 4)
add_tournament("Greenhill", 8)

negPercent = negWs/rounds
negElimPercent = elimNegWs/elims
print("Neg wins " +  str(negPercent) + "%. Rounds: " + str(rounds))
print("Elim Neg wins " +  str(negElimPercent) + "%. Rounds: " + str(elims))

elos = sorted(elos_dict.items(), key=lambda item: item[1], reverse=True)
write_to_csv(elos)
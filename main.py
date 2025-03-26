import glob
import pandas as pd
import numpy as np
import math
from skelo.model.elo import EloEstimator
from skelo.model.glicko2 import Glicko2Estimator
import re

'''
Notes:
Must include file with entries in the tournament folder, then two folders
with all of the prelims and elims in order
'''

# globals -- dd
bidList = {}
elos_dict = {}

# globals -- sidebias
rounds = 0
elims = 0
negWs = 0
elimNegWs = 0

# globals -- glicko
rounds_dict = {}
roundCSV = "tournament,winner_name,winner_school,winner_id,loser_name,loser_school,loser_id,date\n"

# globals -- misc
unifiedEntriesDict = {}
unifiedByName = {}
playerid = 100000
    

def entry_dict(tournament):
    # glicko2 dict
    global unifiedEntriesDict
    global unifiedByName
    global playerid
    
    '''make a dictionary with all of the entries at a tournament with school and names'''
    outputDict = {}
    
    file_location = glob.glob("Documents/Debate/SideBias/" + tournament + "/*.csv")[0]
    teams = pd.read_csv(file_location, delimiter=",", header=0, usecols=[2, 3])
    teams = teams.to_numpy()
    for team in teams:
        
        playerid += 1
        school, name = team[1], team[0]
        # name conflicts
        if name == "Michael Meng":
            if "Lawrenceville" in school:
                name = "Michael Meng (Lawrenceville)"
            else:
                name = "Michael Meng (Strake)"
                
        outputDict[school] = [name, school]
        
    # new names
        if school not in unifiedEntriesDict:
            unifiedEntriesDict[school] = [name, school, playerid]
            unifiedByName[name] = school
    
    print("Processed entries for " + tournament)    
    
    return outputDict


def roundDict(tournament, date):
    global unifiedEntriesDict
    global roundCSV

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
 
            if "neg" in result or "con" in result:
                team1, team2 = team2, team1  # team 1 is the winning team

            try:
                team1, team2 = unifiedEntriesDict[team1], unifiedEntriesDict[team2]
            except:
                continue
            
            name1 = team1[0]
            school1 = team1[1]
            id1 = team1[2]
            name2 = team2[0]
            school2 = team2[1]
            id2 = team2[2]    
            roundCSV += tournament + "," + name1 + "," + school1 + "," + str(id1) + "," + name2 + "," + school2 + "," + str(id2) + "," + str(date) + "\n"

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
            votes = votes.lower()
            
            try:
                margin, result = tuple(result.split())
            except:
                continue
            
            if "bye" in result or "BYE" in team1 or "BYE" in team2 or "BYE" in judge or "bye" in margin:
                continue
            
            if "neg" in result or "con" in result or "aff" not in votes:
                team1, team2 = team2, team1  # team 1 is the winning team

            try:
                team1, team2 = unifiedEntriesDict[team1], unifiedEntriesDict[team2]
            except:
                continue
            
            name1 = team1[0]
            school1 = team1[1]
            id1 = team1[2]
            name2 = team2[0]
            school2 = team2[1]
            id2 = team2[2]  
            roundCSV += tournament + "," + name1 + "," + school1 + "," + str(id1) + "," + name2 + "," + school2 + "," + str(id2) + "," + str(date) + "\n"            
            
    
def roundDictCSV():
    global roundCSV
    
    with open("Documents/Debate/SideBias/Rounds.csv", "w") as fp:
        fp.write(roundCSV[:-1])

def skeloElo():
    global unifiedByName
    
    df = pd.read_csv("Documents/Debate/SideBias/Rounds.csv")
    labels = len(df) * [1]
    
    model = EloEstimator(
        key1_field="winner_name",
        key2_field="loser_name",
        timestamp_field="date",
        initial_time=20240801
    ).fit(df, labels)
    
    eloRankings = model.rating_model.to_frame()
    filterDate = eloRankings['valid_to'].isnull()
    eloRankings = eloRankings[filterDate]
    eloRankings = eloRankings.drop(labels='valid_from', axis=1)
    eloRankings = eloRankings.drop(labels='valid_to', axis=1)
    eloRankings = eloRankings.sort_values(by='rating', ascending=False).reset_index(drop=True)
    eloRankings.index += 1
    
    eloRankings['schoolcol'] = eloRankings['key'].map(unifiedByName)
    eloRankings.to_csv('Documents/Debate/SideBias/elorerank.csv')
    
def skeloGlicko():
    global unifiedByName
    
    df = pd.read_csv("Documents/Debate/SideBias/Rounds.csv")
    labels = len(df) * [1]
    
    model = Glicko2Estimator(
        key1_field="winner_name",
        key2_field="loser_name",
        timestamp_field="date",
        initial_time=20240801
    ).fit(df, labels)
    
    eloRankings = model.rating_model.to_frame()
    
    filterDate = eloRankings['valid_to'].isnull()
    eloRankings = eloRankings[filterDate]
    eloRankings = eloRankings.drop(labels='valid_from', axis=1)
    eloRankings = eloRankings.drop(labels='valid_to', axis=1)
    eloRankings.index += 1
    eloRankings['school'] = eloRankings['key'].map(unifiedByName)
    eloRankings[['rating2', 'rating deviation', 'rating volatility']] = eloRankings['rating'].apply(pd.Series)
    eloRankings.drop(labels='rating', axis=1, inplace=True)
    eloRankings.rename(columns={'rating2' : 'rating'}, inplace=True)
    eloRankings = eloRankings.sort_values(by='rating', ascending=False).reset_index(drop=True)
    eloRankings.index += 1
    
    eloRankings.to_csv('Documents/Debate/SideBias/glickorank.csv')
    

def scuffedGlickoPrelims(tournament, teamsDict, elos_dict, bid):
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
            gsig1 = 1 / (math.sqrt(1 + (3*(sig2**2)/(math.pi**2))))
            ef1 = 1 / (1 + pow(math.e, ((-gsig1) * (mu1 - mu2))))
            v1 = 1 / (pow(gsig1, 2) * ef1 * (1 - ef1))
            d1 = gsig1 * (1 - ef1) # should be 0 - ef1 for a loss
            # glicko would update player volatility here. I'm keeping it constant at .06.
            
            sig1 = math.sqrt(sig1**2 + math.pow(0.06,2))
            sig1 = 1 / math.sqrt((1/sig1) + (1/v1))
            mu1 = mu1 + (sig1**2 * d1)
            
            # player 2 calcs
            gsig2 = 1 / math.sqrt(1 + (3*(sig1**2)/(math.pi**2)))
            ef2 = 1 / (1 + pow(math.e, (-gsig2 * (mu2 - mu1))))
            v2 = 1 / ((gsig2**2) * ef2 * (1-ef2))
            d2 = gsig2 * (0 - ef2) # should be 0 - ef2 for a loss
            # glicko would update player volatility here. I'm keeping it constant at .06.
            
            sig2 = math.sqrt(sig2**2 + math.pow(0.06,2))
            sig2 = 1 / math.sqrt((1/sig2) + (1/v2))
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
    
def scuffedGlickoElims(tournament, teamsDict, elos_dict, bid):
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
            votes = votes.lower()
            
            try:
                margin, result = tuple(result[1:-2].split())
            except:
                continue
            
            if "bye" in result or "BYE" in team1 or "BYE" in team2 or "BYE" in judge or "bye" in margin:
                continue

            rounds += 1
            elims += 1
            
            if "neg" in result or "con" in result or "aff" not in result:
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

def add_tournament(tournament, bid, date):
    '''adds a tournament to the rankings'''
    dictionary = entry_dict(tournament)
    roundDict(tournament, date)
    scuffedGlickoPrelims(tournament, dictionary, elos_dict, bid)
    scuffedGlickoElims(tournament, dictionary, elos_dict, bid)


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
    


# third parameter is for time/weekend. just has to be sequential.
"""
add_tournament("Loyola", 4, 20240830)
add_tournament("SeasonOpener", 4, 20240907)
add_tournament("Grapevine", 4, 20240913)
add_tournament("Yale", 4, 20240920)
add_tournament("MidAmericaCup", 8, 20240927)
add_tournament("JackHowe", 2, 20240928)
add_tournament("Greenhill", 8, 20240919)
add_tournament("NanoNagle", 4, 20241012) 
add_tournament("DTA", 2, 20241012)
add_tournament("JWPatterson", 1, 20241018)
add_tournament("Bronx", 8, 20241018)
add_tournament("Heart of Texas", 8, 20241025)
add_tournament("Meadows", 4, 20241025)
add_tournament("Florida", 4, 20241101)
add_tournament("Apple Valley", 8, 20241108)
add_tournament("Damus", 2, 20241108)
add_tournament("Badgerland", 1, 20241115)
add_tournament("Laird", 1, 20241115)
add_tournament("Glenbrooks", 8, 20241123)
add_tournament("Princeton", 2, 20241206)
add_tournament("TOCDigital1", 2, 20241206)
add_tournament("Alta", 2, 20241206)
add_tournament("LonghornClassic", 4, 20241206)
add_tournament("LaCostaCanyon", 1, 20241206)
add_tournament("Cypress", 1, 20241206)
add_tournament("Ridge", 2, 20241206)
add_tournament("IsidoreNewman", 2, 20241213)
add_tournament("DowlingCatholic", 1, 20241213)
"""

#JF
add_tournament("Blake", 8, 20241220)
add_tournament("CollegePrep", 4, 20241220)
add_tournament("Strake", 2, 20241220)
add_tournament("Newark", 4, 20250110)
add_tournament("ArizonaState", 1, 20250110)
add_tournament("ChurchillClassic", 2, 20250110)
add_tournament("PugetSound", 2, 20250110)
add_tournament("Sunvitational", 1, 20250110)
add_tournament("NorthAllegheny", 1, 20250110)
add_tournament("Peninsula", 4, 20250110)
add_tournament("HarvardWestlake", 8, 20250117)
add_tournament("Durham", 2, 20250117)
add_tournament("MountVernon", 1, 20250117)
add_tournament("UniversityOfHouston", 2, 20250117)
add_tournament("Lexington", 4, 20250117)
add_tournament("Lewis&Clark", 1, 20250117)
add_tournament("Cavalier", 2, 20250117)
add_tournament("Emory", 8, 20250124)
add_tournament("Pennsbury", 2, 20250201)
add_tournament("GoldenDesert", 2, 20250201)
add_tournament("Columbia", 1, 20250201)
add_tournament("UpperStClair", 1, 20250208)
add_tournament("UniversityOfPennsylvania", 1, 20250208)
add_tournament("Stanford", 4, 20250208)
add_tournament("Harvard", 8, 20250215)
add_tournament("Berkeley", 8, 20250215)
add_tournament("TOCDigital2", 4, 20250222)
add_tournament("MillardNorth", 1, 20250228)
add_tournament("USC", 2, 20250228)
add_tournament("TOCDigital3", 4, 20250307)


negPercent = negWs/rounds
negElimPercent = elimNegWs/elims
print("Neg wins " +  str(negPercent) + ". Rounds: "+ str(negWs) + "/" + str(rounds))
print("Elim Neg wins " +  str(negElimPercent) + ". Rounds: " + str(elimNegWs) + "/" + str(elims))

elos = sorted(elos_dict.items(), key=lambda item: item[1], reverse=True)
write_to_csv(elos)

roundDictCSV()
skeloElo()
skeloGlicko()

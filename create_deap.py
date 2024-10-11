import random
import pandas as pd
from deap import base, creator, tools, algorithms
import numpy as np

# Step 1: Read the Excel file and clean the data
file_path = '/Users/sozalp/Downloads/friday_list.xlsx'
player_df = pd.read_excel(file_path)

# Drop unnecessary columns like 'Unnamed: 7' if they exist
if 'Unnamed: 7' in player_df.columns:
    player_df = player_df.drop(columns=['Unnamed: 7'])

# Convert to list of dictionaries
players = player_df.to_dict('records')

# Fitness function to evaluate balance between two teams
def evaluate(individual):
    team1 = individual[:8]  # First 8 players for team 1
    team2 = individual[8:16]  # Next 8 players for team 2
    
    team1_stats = {"skill": 0, "fitness": 0, "vision": 0, "weight": 0, "age": 0, "positions": {"Defender": 0, "Midfielder": 0, "Attacker": 0}}
    team2_stats = {"skill": 0, "fitness": 0, "vision": 0, "weight": 0, "age": 0, "positions": {"Defender": 0, "Midfielder": 0, "Attacker": 0}}
    
    for player in team1:
        team1_stats["skill"] += player["skill_level_5_10"]
        team1_stats["fitness"] += player["fitness_1_10"]
        team1_stats["vision"] += player["vision_5_10"]
        team1_stats["weight"] += player["weight_kg"]
        team1_stats["age"] += player["age"]
        team1_stats["positions"][player["preferred_position"]] += 1
    
    for player in team2:
        team2_stats["skill"] += player["skill_level_5_10"]
        team2_stats["fitness"] += player["fitness_1_10"]
        team2_stats["vision"] += player["vision_5_10"]
        team2_stats["weight"] += player["weight_kg"]
        team2_stats["age"] += player["age"]
        team2_stats["positions"][player["preferred_position"]] += 1

    skill_diff = abs(team1_stats["skill"] - team2_stats["skill"])
    fitness_diff = abs(team1_stats["fitness"] - team2_stats["fitness"])
    vision_diff = abs(team1_stats["vision"] - team2_stats["vision"])
    weight_diff = abs(team1_stats["weight"] - team2_stats["weight"])
    age_diff = abs(team1_stats["age"] - team2_stats["age"])
    
    position_penalty = 0
    for pos in ["Defender", "Midfielder", "Attacker"]:
        position_penalty += abs(team1_stats["positions"][pos] - team2_stats["positions"][pos])

    return skill_diff + fitness_diff + vision_diff + weight_diff + age_diff + position_penalty,

# Setup DEAP
creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
creator.create("Individual", list, fitness=creator.FitnessMin)

toolbox = base.Toolbox()
toolbox.register("indices", random.sample, players, len(players))
toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.indices)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)

toolbox.register("mate", tools.cxTwoPoint)
toolbox.register("mutate", tools.mutShuffleIndexes, indpb=0.05)
toolbox.register("select", tools.selTournament, tournsize=3)
toolbox.register("evaluate", evaluate)

# Genetic Algorithm parameters
population = toolbox.population(n=50)
prob_crossover = 0.7
prob_mutation = 0.2
num_generations = 100

result_population, logbook = algorithms.eaSimple(population, toolbox, cxpb=prob_crossover, mutpb=prob_mutation, ngen=num_generations, verbose=False)

best_individual = tools.selBest(result_population, k=1)[0]

# Ensure two teams of 8 players each
team1 = best_individual[:8]  # First 8 players
team2 = best_individual[8:16]  # Next 8 players

# Output the final teams
print("Best Team 1:")
for player in team1:
    print(player)

print("\nBest Team 2:")
for player in team2:
    print(player)

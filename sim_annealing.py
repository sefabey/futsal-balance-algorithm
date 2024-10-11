import random
import math
import pandas as pd
from copy import deepcopy
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st  # For creating a simple UI
import json

# Load configuration from a local JSON file to retrieve settings for accessing Google Sheets and algorithm parameters
import os

# Determine if the app is running on Streamlit Cloud or locally
if "SHEET_URL" in st.secrets:
    # Load secrets from Streamlit Cloud
    sheet_url = st.secrets["SHEET_URL"]
    creds_dict = {
        "type": st.secrets["CREDENTIALS_TYPE"],
        "project_id": st.secrets["CREDENTIALS_PROJECT_ID"],
        "private_key_id": st.secrets["CREDENTIALS_PRIVATE_KEY_ID"],
        "private_key": st.secrets["CREDENTIALS_PRIVATE_KEY"],
        "client_email": st.secrets["CREDENTIALS_CLIENT_EMAIL"],
        "client_id": st.secrets["CREDENTIALS_CLIENT_ID"],
        "auth_uri": st.secrets["CREDENTIALS_AUTH_URI"],
        "token_uri": st.secrets["CREDENTIALS_TOKEN_URI"],
        "auth_provider_x509_cert_url": st.secrets["CREDENTIALS_AUTH_PROVIDER_X509_CERT_URL"],
        "client_x509_cert_url": st.secrets["CREDENTIALS_CLIENT_X509_CERT_URL"]
    }
else:
    # Load configuration from a local JSON file to retrieve settings for accessing Google Sheets and algorithm parameters
    with open('config.json') as config_file:
    # Example config.json format to be added for reference
    # {
    #     "SHEET_URL": "your_google_sheet_url",
    #     "CREDENTIALS_PATH": "path_to_your_credentials.json",
    #     "INITIAL_TEMP": 1000,
    #     "COOLING_RATE": 0.99,
    #     "MAX_ITERATIONS": 100000
    # }
    config = json.load(config_file)

# Global weights for evaluating team balance - used to determine the relative importance of each player attribute when evaluating team differences
weights = {
    "skill": 0.7,      # Skill is very important
    "fitness": 0.5,    # Fitness is important
    "vision": 0.3,     # Vision is moderately important
    "bmi": 0.3,        # BMI is less important
    "position": 2,     # Position balance is the most important
}

def evaluate_team_balance(team1, team2):
    """
    Evaluate the balance between two teams based on player attributes.
    This function calculates a weighted score based on differences in skill, fitness, vision, BMI, and positional balance.
    A lower score indicates a more balanced set of teams.
    """
    # Calculate weighted differences in total attributes for balance
    skill_diff = abs(sum(player['skill_level_5_10'] for player in team1) - sum(player['skill_level_5_10'] for player in team2)) * weights['skill']
    fitness_diff = abs(sum(player['fitness_1_10'] for player in team1) - sum(player['fitness_1_10'] for player in team2)) * weights['fitness']
    vision_diff = abs(sum(player['vision_5_10'] for player in team1) - sum(player['vision_5_10'] for player in team2)) * weights['vision']
    bmi_diff = abs(sum(player['bmi'] for player in team1) - sum(player['bmi'] for player in team2)) * weights['bmi']
    position_penalty = 0
    for pos in ['Defender', 'Midfielder', 'Attacker', 'Goalkeeper']:
        position_penalty += abs(sum(1 for player in team1 if player['preferred_position'] == pos) - sum(1 for player in team2 if player['preferred_position'] == pos)) * weights['position']
    return skill_diff + fitness_diff + vision_diff + bmi_diff + position_penalty

def simulated_annealing(players, initial_temp, cooling_rate, max_iterations, team_size):
    """
    Use the Simulated Annealing algorithm to find the most balanced team distribution.
    The algorithm iteratively improves team balance by swapping players and allowing controlled randomness to avoid local minima.
    """
    random.shuffle(players)
    team1 = players[:team_size]
    team2 = players[team_size:team_size*2]
    current_score = evaluate_team_balance(team1, team2)
    temp = initial_temp
    best_score = current_score
    best_solution = (deepcopy(team1), deepcopy(team2))
    
    for iteration in range(max_iterations):
        new_team1 = deepcopy(team1)
        new_team2 = deepcopy(team2)
        player1 = random.choice(new_team1)
        player2 = random.choice(new_team2)
        new_team1.remove(player1)
        new_team2.remove(player2)
        new_team1.append(player2)
        new_team2.append(player1)
        new_score = evaluate_team_balance(new_team1, new_team2)
        if new_score < current_score or random.uniform(0, 1) < math.exp((current_score - new_score) / temp):
            team1, team2 = new_team1, new_team2
            current_score = new_score
            if new_score < best_score:
                best_score = new_score
                best_solution = (deepcopy(new_team1), deepcopy(new_team2))
        temp *= cooling_rate
    
    return best_solution, best_score

@st.cache_data(show_spinner=False)
# Cache the data to avoid repeatedly fetching it from Google Sheets, improving performance
def load_player_data_from_google_sheet(sheet_url):
    """
    Load player data from a Google Sheet.
    Authenticates using Google Service Account credentials and returns player data as a list of dictionaries.
    """
    # Authenticate and load data from Google Sheets
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets",
             "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)

    # Open the sheet by URL
    sheet = client.open_by_url(sheet_url)
    worksheet = sheet.worksheet("Roster")

    # Convert to a pandas DataFrame
    data = worksheet.get_all_records()
    player_df = pd.DataFrame(data)
    return player_df.to_dict('records')

def main():
    """
    Main function to run the Streamlit interface for selecting futsal teams.
    Allows users to select players and runs the Simulated Annealing algorithm to balance the teams.
    """
    # Use the appropriate Google Sheets URL based on the environment
    sheet_url = config['SHEET_URL'] if 'SHEET_URL' not in st.secrets else st.secrets['SHEET_URL']

    # Load player data
    players = load_player_data_from_google_sheet(sheet_url)

    # Create a simple interface using Streamlit
    st.title("Futsal Team Selection Application")
    # Display the title of the Streamlit application

    # Display player list and select participants
    player_df = pd.DataFrame(players)
    st.write("Please select the participants for the upcoming match:")

    # Multi-select for player names
    selected_players = st.multiselect("Choose players:", player_df["player_name"])
    st.write(f"Total players selected: {len(selected_players)}")
    # Inform the user how many players have been selected

    # Filter selected players based on their names
    participants = [player for player in players if player["player_name"] in selected_players]
    total_players = len(participants)

    # Check if selected number of players is 16 or 18
    if total_players not in [16, 18]:
        st.warning(f"Warning: You have selected {total_players} players.")
        st.error("Error: Please select either 16 or 18 players to proceed.")
    else:
        # Calculate team size dynamically based on the total number of players
        team_size = total_players // 2

        # Simulated Annealing Parameters
        initial_temp = config.get('INITIAL_TEMP', 1000)  # Initial temperature
        cooling_rate = config.get('COOLING_RATE', 0.99)  # Cooling rate
        max_iterations = config.get('MAX_ITERATIONS', 100000)  # Maximum number of iterations

        # Run the Simulated Annealing algorithm to balance the teams
        best_teams, best_score = simulated_annealing(participants, initial_temp, cooling_rate, max_iterations, team_size)
        team1, team2 = best_teams

        # Print the teams on the Streamlit UI
        st.subheader("Team 1 - Balanced Players:")
        for player in team1:
            st.text(f"{player['player_name']} - {player['preferred_position']}")

        st.subheader("Team 2 - Balanced Players:")
        for player in team2:
            st.text(f"{player['player_name']} - {player['preferred_position']}")

        st.subheader(f"Team Balance Score (Lower is Better): {best_score}")

# Run the main function when the script is executed
if __name__ == "__main__":
    main()
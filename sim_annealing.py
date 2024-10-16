import random
import math
import pandas as pd
from copy import deepcopy
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st  # For creating a simple UI
import json
import os

#random seed fix
random.seed(42)

# Determine if the app is running on Streamlit Cloud by checking if Streamlit secrets are available
is_streamlit_cloud = False
try:
    # Attempt to access st.secrets, if it exists, we are on Streamlit Cloud
    if st.secrets._secrets is not None:
        is_streamlit_cloud = True
except Exception:
    # If st.secrets does not exist or any exception occurs, we're running locally
    is_streamlit_cloud = False

if is_streamlit_cloud:  # Check if the app is running in Streamlit Cloud
    try:
        # Load secrets from Streamlit Cloud
        sheet_url = st.secrets.get("SHEET_URL")
        creds_dict = {
            "type": st.secrets.get("CREDENTIALS_TYPE"),
            "project_id": st.secrets.get("CREDENTIALS_PROJECT_ID"),
            "private_key_id": st.secrets.get("CREDENTIALS_PRIVATE_KEY_ID"),
            "private_key": st.secrets.get("CREDENTIALS_PRIVATE_KEY"),
            "client_email": st.secrets.get("CREDENTIALS_CLIENT_EMAIL"),
            "client_id": st.secrets.get("CREDENTIALS_CLIENT_ID"),
            "auth_uri": st.secrets.get("CREDENTIALS_AUTH_URI"),
            "token_uri": st.secrets.get("CREDENTIALS_TOKEN_URI"),
            "auth_provider_x509_cert_url": st.secrets.get("CREDENTIALS_AUTH_PROVIDER_X509_CERT_URL"),
            "client_x509_cert_url": st.secrets.get("CREDENTIALS_CLIENT_X509_CERT_URL")
        }
        username = st.secrets.get("USERNAME")
        password = st.secrets.get("PASSWORD")
    except Exception as e:
        st.error("Error loading secrets from Streamlit Cloud.")
        st.stop()  # Stop execution if secrets cannot be loaded
else:
    # Load configuration from a local JSON file to retrieve settings for accessing Google Sheets and algorithm parameters
    try:
        with open('config.json') as config_file:
            config = json.load(config_file)
        sheet_url = config.get("SHEET_URL")
        creds_path = config.get("CREDENTIALS_PATH")
        username = config.get("USERNAME")
        password = config.get("PASSWORD")

        # Load credentials from the JSON file locally
        with open(creds_path) as f:
            creds_dict = json.load(f)
    except FileNotFoundError:
        st.error("Local configuration file not found.")
        st.stop()  # Stop execution if config file is missing
    except KeyError as e:
        st.error("Missing configuration value.")
        st.stop()  # Stop execution if any configuration value is missing

# Authentication to Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

# Create credentials for Google Sheets API using provided credentials
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)  # Authorize the client to interact with Google Sheets

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
    
    # Calculate positional imbalance penalty
    position_penalty = 0
    for pos in ['Defender', 'Midfielder', 'Attacker', 'Goalkeeper']:
        # Calculate the difference in number of players per position between the two teams
        position_penalty += abs(sum(1 for player in team1 if player['preferred_position'] == pos) - sum(1 for player in team2 if player['preferred_position'] == pos)) * weights['position']
    
    # Return the total imbalance score
    return skill_diff + fitness_diff + vision_diff + bmi_diff + position_penalty

def simulated_annealing(players, initial_temp, cooling_rate, max_iterations, team_size):
    """
    Use the Simulated Annealing algorithm to find the most balanced team distribution.
    The algorithm iteratively improves team balance by swapping players and allowing controlled randomness to avoid local minima.
    """
    # Randomly shuffle players to create initial teams
    random.shuffle(players)
    team1 = players[:team_size]
    team2 = players[team_size:team_size*2]
    current_score = evaluate_team_balance(team1, team2)
    temp = initial_temp  # Set initial temperature for simulated annealing
    best_score = current_score
    best_solution = (deepcopy(team1), deepcopy(team2))
    
    for iteration in range(max_iterations):
        # Create a new potential solution by swapping players between teams
        new_team1 = deepcopy(team1)
        new_team2 = deepcopy(team2)
        player1 = random.choice(new_team1)
        player2 = random.choice(new_team2)
        new_team1.remove(player1)
        new_team2.remove(player2)
        new_team1.append(player2)
        new_team2.append(player1)
        
        # Calculate the score of the new team configuration
        new_score = evaluate_team_balance(new_team1, new_team2)
        
        # Accept the new configuration if it improves the score or based on a probability function
        if new_score < current_score or random.uniform(0, 1) < math.exp((current_score - new_score) / temp):
            team1, team2 = new_team1, new_team2
            current_score = new_score
            # Update the best solution if the new score is better
            if new_score < best_score:
                best_score = new_score
                best_solution = (deepcopy(new_team1), deepcopy(new_team2))
        
        # Decrease the temperature to reduce the probability of accepting worse solutions
        temp *= cooling_rate
    
    return best_solution, best_score

@st.cache_data(show_spinner=False)
# Cache the data to avoid repeatedly fetching it from Google Sheets, improving performance
def load_player_data_from_google_sheet(sheet_url):
    """
    Load player data from a Google Sheet.
    Authenticates using Google Service Account credentials and returns player data as a list of dictionaries.
    """
    # Open the sheet by URL and select the worksheet
    sheet = client.open_by_url(sheet_url)
    worksheet = sheet.worksheet("Roster")

    # Retrieve all records from the worksheet and convert to a pandas DataFrame
    data = worksheet.get_all_records()
    player_df = pd.DataFrame(data)
    return player_df.to_dict('records')  # Return the player data as a list of dictionaries

def main():
    """
    Main function to run the Streamlit interface for selecting futsal teams.
    Allows users to select players and runs the Simulated Annealing algorithm to balance the teams.
    """
    # Simple login system to secure access
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False

    if not st.session_state['authenticated']:
        # Input fields for username and password
        input_username = st.text_input("Username", key='username_input')
        input_password = st.text_input("Password", type="password", key='password_input')
        if st.button("Login"):
            # Check credentials
            if input_username == username and input_password == password:
                st.session_state['authenticated'] = True
                st.success("Login successful")
            else:
                st.error("Incorrect username or password. Please try again.")
        # Stop the execution here until the user successfully logs in
        return

    # Only proceed with the rest of the application if the user is authenticated
    # Load player data from Google Sheet
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
        initial_temp = 1000  # Initial temperature
        cooling_rate = 0.99  # Cooling rate
        max_iterations = 100000  # Maximum number of iterations

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
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

is_streamlit_cloud = False
try:
    if st.secrets._secrets is not None:
        is_streamlit_cloud = True
except Exception:
    is_streamlit_cloud = False

if is_streamlit_cloud:
    try:
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
        st.stop()
else:
    try:
        with open('config.json') as config_file:
            config = json.load(config_file)
        sheet_url = config.get("SHEET_URL")
        creds_path = config.get("CREDENTIALS_PATH")
        username = config.get("USERNAME")
        password = config.get("PASSWORD")
        with open(creds_path) as f:
            creds_dict = json.load(f)
    except FileNotFoundError:
        st.error("Local configuration file not found.")
        st.stop()
    except KeyError as e:
        st.error("Missing configuration value.")
        st.stop()

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

weights = {
    "skill": 1,
    "fitness": 0.6,
    "vision": 0.5,
    "bmi": 0.3,
    "position": 2,
    "age": 0.3
}

def evaluate_team_balance(team1, team2):
    skill_diff = abs(sum(player['skill_level_5_10'] for player in team1) - sum(player['skill_level_5_10'] for player in team2)) * weights['skill']
    fitness_diff = abs(sum(player['fitness_1_10'] for player in team1) - sum(player['fitness_1_10'] for player in team2)) * weights['fitness']
    vision_diff = abs(sum(player['vision_5_10'] for player in team1) - sum(player['vision_5_10'] for player in team2)) * weights['vision']
    bmi_diff = abs(sum(player['bmi'] for player in team1) - sum(player['bmi'] for player in team2)) * weights['bmi']
    age_diff = abs(sum(player['age'] for player in team1) - sum(player['age'] for player in team2)) * weights['age']
    position_penalty = 0
    for pos in ['Defender', 'Midfielder', 'Attacker', 'Goalkeeper']:
        position_penalty += abs(sum(1 for player in team1 if player['preferred_position'] == pos) - sum(1 for player in team2 if player['preferred_position'] == pos)) * weights['position']
    return skill_diff + fitness_diff + vision_diff + bmi_diff + age_diff + position_penalty

def simulated_annealing(players, initial_temp, cooling_rate, max_iterations, team_size):
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
def load_player_data_from_google_sheet(sheet_url):
    sheet = client.open_by_url(sheet_url)
    worksheet = sheet.worksheet("Roster")
    data = worksheet.get_all_records()
    player_df = pd.DataFrame(data)
    return player_df.to_dict('records')

def main():
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False

    if not st.session_state['authenticated']:
        input_username = st.text_input("Username", key='username_input')
        input_password = st.text_input("Password", type="password", key='password_input')
        if st.button("Login"):
            if input_username == username and input_password == password:
                st.session_state['authenticated'] = True
                st.success("Login successful")
            else:
                st.error("Incorrect username or password. Please try again.")
        return

    players = load_player_data_from_google_sheet(sheet_url)
    st.title("Futsal Team Selection Application")
    st.write("Please select the participants for the upcoming match:")
    player_df = pd.DataFrame(players)
    selected_players = st.multiselect("Choose players:", player_df["player_name"])
    st.write(f"Total players selected: {len(selected_players)}")
    participants = [player for player in players if player["player_name"] in selected_players]
    total_players = len(participants)

    if total_players not in [16, 18]:
        st.warning(f"Warning: You have selected {total_players} players.")
        st.error("Error: Please select either 16 or 18 players to proceed.")
    else:
        team_size = total_players // 2
        initial_temp = 1000
        cooling_rate = 0.99
        max_iterations = 100000
        best_teams, best_score = simulated_annealing(participants, initial_temp, cooling_rate, max_iterations, team_size)
        team1, team2 = best_teams
        st.subheader("Team 1 - Balanced Players:")
        for player in team1:
            st.text(f"{player['player_name']} - {player['preferred_position']}")
        st.subheader("Team 2 - Balanced Players:")
        for player in team2:
            st.text(f"{player['player_name']} - {player['preferred_position']}")
        st.subheader(f"Team Balance Score (Lower is Better): {best_score}")

if __name__ == "__main__":
    main()

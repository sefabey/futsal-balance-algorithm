# Futsal Team Selection Application

## Overview
This project is a **Futsal Team Selection Application** that allows you to easily select participants for a futsal match and create balanced teams using a **simulated annealing** algorithm. The application uses player data from a Google Sheets document, making it easy to maintain, update, and select players for each match. The project is built using Python, **Streamlit** for the user interface, and **Google Sheets API** for data access.

## Features
- **Integration with Google Sheets**: Player data is dynamically loaded from a Google Sheet, which makes it easy to update without modifying the code.
- **Simple User Interface**: Users can select players for the match through a web-based interface using **Streamlit**.
- **Balanced Team Generation**: The **simulated annealing** algorithm ensures that the selected teams are well-balanced based on player attributes such as skill level, fitness, vision, BMI, and position.

## Prerequisites
- **Conda** installed for creating a virtual environment.
- **Python 3.9** or higher.
- **Google Cloud Service Account** with credentials JSON file.

## Setup Instructions

### Step 1: Clone the Repository
Clone this repository to your local machine:

```sh
git clone https://github.com/sefabey/futsal-balance-algorithm.git
cd futsal_team_selection
```

### Step 2: Create a Conda Environment
Create a new Conda environment to manage dependencies:

```sh
conda create --name futsal_teams python=3.9
```

Activate the environment:

```sh
conda activate futsal_teams
```

### Step 3: Install Dependencies
Install required dependencies:

1. Install **pandas** using Conda:

   ```sh
   conda install pandas
   ```

2. Install other dependencies using **pip**:

   ```sh
   pip install gspread oauth2client streamlit
   ```

### Step 4: Set Up Google Service Account
1. **Create a Google Cloud Service Account**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/).
   - Navigate to **IAM & Admin > Service Accounts**.
   - Click **Create Service Account**.
     - Provide a name for your service account.
     - Optionally, provide a description.
   - After creating the service account, click **Create Key**.
     - Choose **JSON** as the key type.
     - Download the credentials JSON file that gets generated.
   - Save this file in the root directory of your project and rename it to `credentials.json`.

2. **Grant Access to Google Sheets**:
   - Open the Google Sheet containing the player data by following the provided link.
   - Click **Share** and enter the **service account email address** to grant read access.

### Step 5: Create a Configuration File
Create a `config.json` file in the root directory of the project. This file will contain placeholders for accessing Google Sheets and configuring the simulated annealing algorithm. Below is an example of the `config.json` file format:

```json
{
    "SHEET_URL": "<YOUR_GOOGLE_SHEET_URL>",
    "CREDENTIALS_PATH": "<PATH_TO_YOUR_CREDENTIALS.json>",
    "INITIAL_TEMP": 1000,
    "COOLING_RATE": 0.99,
    "MAX_ITERATIONS": 100000
}
```

Make sure to replace the **SHEET_URL** and **CREDENTIALS_PATH** values with the actual Google Sheet URL and the path to your credentials file. **Do not include sensitive information in public repositories.**

### Step 6: Run the Application
To run the Streamlit application, execute the following command:

```sh
streamlit run futsal_team_selection.py
```

This command will start a local server and provide a link to open the app in your web browser. You can use this interface to select participants for the futsal match and generate balanced teams.

## Usage Instructions
1. Open the link provided by **Streamlit** after starting the server.
2. Use the **multi-select widget** to select 16 or 18 players for the match.
3. The app will automatically balance the teams based on player attributes and display the team lists.

## Project Structure
- **futsal_team_selection.py**: Main application script.
- **config.json**: Configuration file containing Google Sheets URL, credentials path, and algorithm parameters (ensure this file contains no sensitive information before sharing).
- **credentials.json**: Google Service Account credentials for accessing the Google Sheets document (not included, needs to be set up as per instructions).

## License
This project is licensed under a **Non-Commercial Use Only License**. The software may be used for educational or research purposes only, and any commercial use is strictly prohibited without prior permission. Proper citation of the author is required for any use or distribution. See the `LICENSE` file for more details.

## Important Notes
- Ensure that you have **16 or 18 players** selected; otherwise, the app will display an error message.
- The **simulated annealing** algorithm will run to generate the most balanced teams based on the players' attributes.

## Dependencies
- **Python 3.9+**
- **pandas**: For data manipulation.
- **gspread**: For Google Sheets access.
- **oauth2client**: For Google API authentication.
- **Streamlit**: For creating a simple web-based interface.

To install all the dependencies in one go, use the following commands after activating the Conda environment:

```sh
conda install pandas
pip install gspread oauth2client streamlit
```

## Acknowledgements
- **Streamlit** for providing an easy way to create user interfaces.
- **Google Cloud** for enabling access to data via Google Sheets.
- Inspiration for using **simulated annealing** for team balancing.

## Troubleshooting
- **Error Authenticating Google Sheets**: Make sure the **service account email** has been shared with the Google Sheet and that the credentials JSON file is in the correct location.
- **Environment Issues**: Ensure you have activated the correct Conda environment with all dependencies installed.

## Contact
For issues or contributions, please reach out to me or open an issue in the GitHub repository.
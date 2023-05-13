import tkinter
import customtkinter as ctk
import requests
import openai
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

openai.api_key = config.get('OpenAI', 'API_KEY')

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Match Analysis Assistant")

personaname = tkinter.StringVar()
match_id = tkinter.StringVar()

def clean_player_data(player_data):
    # Define the fields that we want to keep
    keep_fields = {
        'hero_id', 'kills', 'deaths', 'assists', 'xp_per_min', 'gold_per_min', 
        'hero_damage', 'hero_healing', 'tower_damage', 'level', 'last_hits'
    }

    # Create a new dictionary with only the fields that we want to keep
    cleaned_data = {field: player_data[field] for field in keep_fields if field in player_data}

    return cleaned_data

def get_match_details():
    match_id = match_id_entry.get()
    url = f"https://api.opendota.com/api/matches/{match_id}"
    response = requests.get(url)

    if response.status_code == 200:
        match_json = response.json()
        ask_gpt3(match_json)
    else:
        print(f"Request failed with status code {response.status_code}")

def ask_gpt3(match_json):
    personaname = player_id_entry.get()
    player_data = None

    # Search for the player with the matching personaname
    for player in match_json['players']:
        if 'personaname' in player and player['personaname'] == personaname:
            player_data = player
            break

    # Clean up all players' data, including the player of interest
    cleaned_players_data = [clean_player_data(player) for player in match_json['players'] if 'personaname' in player]
    
    if player_data is not None:
        cleaned_player_data = clean_player_data(player_data)
        combined_question = f"This is the match you will analyze. The players' data is {cleaned_players_data}. You are providing your services for player {personaname}, whose data is {cleaned_player_data}"
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"You are a helpful and expert Dota 2 coach. You provide excellent analysis of matches provided to you in json format, and provide thorough improvement plans that dont cover basics, but rather in-depth topics, all while also taking a reassuring tone."},
                {"role": "user", "content": combined_question}
            ]
        )
        response_content = response['choices'][0]['message']['content']
        
        # insert the response at the end of the text box
       # response_text.insert(tkinter.END, response_content)
        #response_text(text= f"{response_content}")
        response_text.configure(text= f"{response_content}")
    else:
        print("No player found with the given personaname in the match.")

app_title = ctk.CTkLabel(app, text="Match Analysis Assistant", font=("Arial", 20, "bold"))
app_title.grid(row=0, column=0, columnspan=2, pady=10)

player_id_lbl = ctk.CTkLabel(app, text="Player ID", pady= 10, padx= 10)
player_id_lbl.grid(row=1, column=0)
player_id_entry = ctk.CTkEntry(app)
player_id_entry.grid(row=1, column=1)

match_id_lbl = ctk.CTkLabel(app, text="Match ID", pady= 10, padx= 10)
match_id_lbl.grid(row=2, column=0)
match_id_entry = ctk.CTkEntry(app)
match_id_entry.grid(row=2, column=1)

submit_button = ctk.CTkButton(app, text="Ask", command=get_match_details)
submit_button.grid(row=3, column=0, pady=10, padx=10)

response_box = ctk.CTkScrollableFrame(app, width=300, height=400)
response_box.grid(row=4, column=0, columnspan=4)

response_text = ctk.CTkLabel(response_box, text="", wraplength=300)
response_text.pack()
app.mainloop()

import requests
from bs4 import BeautifulSoup
import pandas as pd

class PitchFX():
    
    def __init__(self):
        self.base_url = "http://gd2.mlb.com/components/game/mlb/"
    
    def get_gameday_gids(self, start, end=None):
        """
        gets a list of game id strings representing all the games played between (and including) the start and end. 
        start and end could be datetime or strings representing dates
        """
        if end is None:
            end = start
            
        game_gids = []
        for date in pd.date_range(start=start, end=end, freq="d"):
            try:
                year = str(date.year)
                month = str(date.month).zfill(2)
                day = str(date.day).zfill(2)
                day_url = self._build_url(year, month, day)
                soup = BeautifulSoup(requests.get(day_url).text)
                game_gids += [ node.get('href').split('/')[1] for node in soup.find_all('a') if 'gid' in node.get('href') ]
            except Exception as e:
                print(f"there was an error at {date} date")
                print(e)
        return game_gids
    
    def get_video_url(self, df):
        """
        replaces play_guid with a clickable video url of the play on baseballsavant.mlb.com
        """
        df["url"] = df.play_guid.apply(
            lambda play_guid: f"https://baseballsavant.mlb.com/sporty-videos?playId={play_guid}"
        )
        
        return df.reset_index().style.format({'url': lambda x: f'<a target="_blank" href="{x}">{x}</a>' })

    
    def get_gid_df(self, gid):
        """
        returns a dataframe with the pitchfx data for the game
        use get_gameday_gids to find the gid by date
        figure about 10 seconds to pull each game, keep that in mind for large date ranges
        """
        return self._parse_json(self._get_game_event_json(gid))
    
    def _parse_json(self, game_events_json):
        """
        parses the nested json object to produce a dataframe for each pitch. 
        game level and atbat level data gets repeated per pitch, don't aggregate
        """
        # TODO ripe for refactoring
        # atbat level columns we'll want to capture
        atbat_cols = ['num', 'away_team_runs', 'home_team_runs','play_guid', 
                      'event', 'event_num', 'des','p_throws', 'pitcher', 'b_height', 
                      'stand', 'batter', 'end_tfs_zulu', 'start_tfs_zulu', 'start_tfs', 
                      'o', 's', 'b']
        
        # get the game id
        gid_parsed = game_events_json["subject"].replace("boxscore_mlb", "gid")
        
        # a list to hold our pitch dataframes
        game_atbat_pitch_data = []
        
        # loop through inning
        for inning in game_events_json["data"]["game"]["inning"]:
            inn_num = inning["num"]
            inn_home_team = inning["home_team"]
            inn_away_team = inning["away_team"]
            
            # account for innings not having a bottom half
            half_innings = ["top", "bottom"] if inning.get("bottom") else ["top"]

            # loop through top and bottom of each inning
            for half_inning in half_innings:
                
                # Loop through each atbat and create series relevant to that half inning
                for atbat in inning[half_inning]["atbat"]:
                    
                    # grab the atbat data and add the game and inning stuff to it
                    atbat_data = pd.Series(atbat)[atbat_cols].rename(lambda x: f"atbat_{x}")
                    
                    # well use this 'key' to hack together the pitch and atbat data
                    atbat_data["key"] = "my_random_key"
                    atbat_data["gid"] = gid_parsed
                    atbat_data["inn_num"] = inn_num
                    atbat_data["home_team"] = inn_home_team
                    atbat_data["away_team"] = inn_away_team
                    atbat_data["half_inning"] = half_inning
                    
                    # now build a dataframe of each pitch
                    
                    # handle single pitch atbats
                    if not isinstance(atbat["pitch"], list):
                        pitches = [atbat["pitch"]]
                    else:
                        pitches = atbat["pitch"]
                        
                    for pitch in pitches:
                        pitch_data = pd.DataFrame([pitch])
                        
                        # tack on the higher level data
                        pitch_data["key"] = "my_random_key"
                        pitch_data = pd.merge(pitch_data, atbat_data.to_frame().T, on="key", how="outer")
                        pitch_data = pitch_data.drop("key", axis=1)
                        
                        # stuff the data into a list to be smushed together at the end
                        game_atbat_pitch_data.append(pitch_data)
        
        # concat all the data into one dataframe and return
        return pd.concat(game_atbat_pitch_data)

    def _get_game_event_json(self, gid):
        """
        helper function that takes a game id string and pulls down the game_events.json dictionary for that game
        """
        full_url = f"{self._build_url(*gid.split('_')[1:4])}/{gid}/game_events.json"
        return requests.get(full_url).json()
        
    def _build_url(self, year, month, day):
        """
        helper function to build the url base
        """
        return f"{self.base_url}year_{year}/month_{month}/day_{day}"
import openai
import os
from google.cloud import texttospeech
import json
import freesound
import time
from pydub import AudioSegment
import random
import sys
from google.oauth2 import service_account
from templates import *
from dotenv import load_dotenv

# load secret keys from .env file
load_dotenv()

SOUND_API_KEY = os.getenv("SOUND_API_KEY")

# API credentials for text to speech | https://developers.google.com/workspace/guides/create-credentials
google_credentials = service_account.Credentials.from_service_account_file(
    'google_auth.json'
)

def save_json(series_title: str, series_dict: dict):
  """Creates a directory for the series if it doesn't exist and saves series dict."""
  folder_path = series_title
  os.makedirs(folder_path, exist_ok=True)
  file_path = os.path.join(folder_path, series_title + ".json")
  with open(file_path, "w") as f:
      json.dump(series_dict, f)
#   print(f'\nShow JSON saved to /{file_path}')

def load_series_dict(series_title: str) -> dict:
    "Loads series dict from title."
    folder_path = series_title
    file_path = os.path.join(folder_path, series_title + ".json")
    with open(file_path, "r") as f:
        series_dict = json.load(f)
    return series_dict

def check_voices(series_dict):
    """If ChatGPT generates invalid voice, assigns random voice."""
    # list of valid voice names as of Aug 2023
    valid_voice_names = [f'en-US-Neural2-{char}' for char in 'ACDEFGHIJ']
    # iterate over copy of characters dict
    for character_name, character_info in series_dict["characters"].copy().items():
        # assigns random valid voice
        random_voice_name = random.choice(valid_voice_names)
        character_voice = character_info['voice']
        # checks if voice is invalid
        if character_voice['name'] not in valid_voice_names:
            # reassign voice to standard
            series_dict['characters'][character_name]['voice']['name'] = random_voice_name
            series_dict['characters'][character_name]['voice']['languageCode'] = 'en-US'
            series_dict['characters'][character_name]['audioConfig'] = {
                "pitch": 0.0,
                "speakingRate": 1
                }
    return series_dict

def generate_season_outline(description: str, sponsor: str, season: int=1, series_title: str="") -> dict:
    """Takes in show description, sponsor, and title and returns season dict with one season outline for new show."""

    # clear terminal screen
    os.system('clear')
    print("\nThank you for trying SeriesGPT!\n")
    
    format = f"""
    Return the information in the form of a JSON string with this format. Don't forget to put character
    voices in this format.: {season_outline_template_string}
    """

    # prompt instructions for generating show information
    instructions = f"""Generate an outline of 10 episodes for a podcast serialized audio show
    include a title {series_title} in the title key. Don't add any new keys, add values for
    episode titles and detailed episode descriptions only for season {season}. """
    theme = "Theme music search term should match the mood of the show overall. "
    sponsor_music = "Sponsor music search term should match the sponsor product. "
    character_instructions = """Character descriptions should only be added to the 'characters' key. Character
    names should be all lower case and may have spaces. Example character name: 'steve smith' 
    Character voices should be distinct, not have accents, and follow the format provided.
    Character voices should be 'en-US-Neural2-A' with only A, D, I, J for male and only C, E, F, G, H, for female.
    No other voices should be used other than those listed here.
    Characters voices should have raised or lowered pitch and speed to match character traits. """

    # final prompt
    prompt = instructions + character_instructions + description + theme + sponsor_music + format

    print(f"\n{'-' * 100}\n\nStep 1: Generating season outline for '{series_title}' sponsored by {sponsor}. This should take about a minute.\n")

    while True:
        try:
            # Request chat response from Chat GPT 3.5
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Extract response
            response = completion.choices[0].message['content']

            try:
                # Create the series_dict and perform additional processing
                series_dict = json.loads(response)

                # Save original description
                series_dict["original description"] = description

                # Dictionary of episode names and descriptions
                episodes_dict = series_dict["seasons"][f"s{season}"]["episodes"]

                # Create list of episode descriptions
                season_outline = []

                # Add episode descriptions to list
                for episode, info in episodes_dict.items():
                    season_outline.append(f"{episode} {info['episode description']}")

                # Save original season outline to resend during episode creation
                series_dict["seasons"][f"s{season}"]["season outline"] = season_outline

                # Record sponsor to dict
                series_dict["sponsor"] = sponsor

                # Assign invalid voices to random voice name
                series_dict = check_voices(series_dict)

                # Make sure character names have spaces instead of underscores
                series_dict["characters"] = {name.replace("_", " "): value for name, value in series_dict["characters"].items()}

                # Save dict
                save_json(series_dict["series title"], series_dict)

            except json.JSONDecodeError:
                # If response cannot be parsed as JSON, resend the request
                print("JSON parsing failed. Trying again...")
                # print(response) # uncomment to print response that caused json parsing error for debugging
                continue

            # Return the updated series_dict
            return series_dict

        except Exception as e:
            # Handle other exceptions, retry the request
            print("Error requesting chat completion:", e)
            print("Retrying request...")


def generate_episode_outline(series_dict: dict, season_num: int, episode_num: int):
    """Takes in series dict, generates one episode outline, and saves updated series dict as json"""
    season_key = 's{}'.format(season_num)
    episode_key = 'e{}'.format(episode_num)

    # create aliases for convenience
    series_title = series_dict['series title']
    episode_data = series_dict['seasons'][season_key]['episodes'][episode_key]
    episode_title = episode_data['episode title']
    episode_description = episode_data['episode description']
    characters_dict = series_dict['characters']
    season_outline = series_dict["seasons"][f"s{season_num}"]["season outline"]

    print(f"\n{'-' * 100}\n\nStep 2: Generating episode outline for {series_title}: s{season_num}e{episode_num} - {episode_title}. This should take about a minute.")

    # prompt instructions for generating scene outline
    instruction_prompt = f"""Create a detailed description for each of 10 scenes for
    season {season_key} episode {episode_key}. Leaves the 'scene' keys blank. episode
    description for the scene must include which characters are being introduced for the first time. """
    episode_prompt = f"""This episode title is {episode_title} in which {episode_description}
    The outline for the rest of the season is {season_outline}. """
    characters_prompt = f"""Current characters are {characters_dict}. Character descriptions
    should be updated to reflect growth. New characters added must have descriptions
    and voices formatted like example. New characters must be added in the exact same format
    as existing characters. New characters should have creative names.
    Make sure to include new characters in the 'characters' key. Remember, characters need real names
    and should not be called 'character 1'"""
    format_prompt = f"Return a json object formatted like {scene_outline_template_string}. "

    # Final prompt
    prompt = instruction_prompt + episode_prompt + characters_prompt + format_prompt + scene_outline_template_string

    while True:
        try:
            # Request chat response from Chat GPT 3.5
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            response = completion.choices[0].message['content']

            try:
                # Parsing the response as a dictionary
                response_dict = json.loads(response)

                # Update the series_dict with the episode key and character key
                series_dict['seasons'][season_key]['episodes'][episode_key]['scenes'] = response_dict.get('scenes', {})
                series_dict['characters'] = response_dict.get('characters', {})

                # Make sure character names have spaces instead of underscores
                series_dict["characters"] = {name.replace("_", " "): value for name, value in series_dict["characters"].items()}

                # print which outline was generated
                print(f'\n{series_title} s{season_num} e{episode_num} - {episode_title} outline added.')

                # Return response
                save_json(series_dict["series title"], series_dict)

                return series_dict

            except json.JSONDecodeError as e:
                print("Error decoding JSON response:", e)
                print("Retrying request...")
                # print(response) # uncomment to print response that caused json parsing error for debugging

        except Exception as e:
            print("Error requesting chat completion:", e)
            print("Retrying request...")

def generate_scene_script(series_dict: dict, season_num: int, episode_num: int, scene_num: int):
    """Takes as inputs series dict and scene number, generates scene script, and resaves series dict to json."""
    past_scene_descriptions = []
    future_scene_descriptions = []
    # alias to episode scenes dictionary
    scenes_dict = series_dict["seasons"][f"s{season_num}"]["episodes"][f"e{episode_num}"]["scenes"]

    # iterate over episode's scenes dictionary
    for scene, info in scenes_dict.items():
        # get scene num as int from key | ex: 'sc4' -> 4
        scene_num_int = int(scene[2:])
        # adds each scene description to list of what came before and after current scene
        if scene_num_int < scene_num:
            past_scene_descriptions.append(info['scene description'])
        else:
            future_scene_descriptions.append(info['scene description'])

    # create aliases for convenience
    current_scene_description = str(series_dict["seasons"][f"s{season_num}"]["episodes"][f"e{episode_num}"]["scenes"][f"sc{scene_num}"]["scene description"])
    series_title = series_dict["series title"]
    episode_title = series_dict["seasons"][f"s{season_num}"]["episodes"][f"e{episode_num}"]["episode title"]
    episode_description = series_dict["seasons"][f"s{season_num}"]["episodes"][f"e{episode_num}"]["episode description"]
    sponsor = series_dict["sponsor"]
    characters = series_dict["characters"]

    # Extract the first two elements from the characters dict and convert them into a list of tuples
    main_character_list = list(characters.items())[:2]

    # Create a main characters dict from the list of tuples
    main_characters = dict(main_character_list)

    # Create a list of host names
    hosts_list = list(main_characters.keys())

    print(f"\n{'-' * 100}\n\nStep 3: Generating script for {series_title}: s{season_num}e{episode_num}sc{scene_num}. This should take about a minute.")

    # scene 1 is an intro
    if scene_num == 1:
        instructions = f"""Write a fun introduction to the audio show {series_title} spoken only by {hosts_list} They should speak about
        how the show was created using artificial intelligence solely from a few sentence prompt. even the music, sound, effects,
        ambience, and voices were chosen by ai. The voices were also generated by ai. They should invite the listener to enjoy the
        current episode enititled {episode_title}. Just talk about how the show was made with ai and give tiny little teaser hints
        about whats going to happen in this episode, which is {episode_description}. Don't start telling the story yet. """
    # scene 6 is an advertisement
    elif scene_num == 6:
        instructions = f"""Write a fun advertisement dialogue between two main characters {hosts_list} where they advertise the show
        sponsor {sponsor}. Even if the product is made up, they should talk gratuitously about how great the product is and how they
        use it constantly. At the end, they should say now back to the show. """
    # scene 10 is an outro
    elif scene_num == 10:
        instructions = f"""Write a show outro instead of a scene. It should be a fun and inviting dialogue between two main characters
        {main_characters} where they thank you for listening to {series_title} and invite the audience to tune in for the next episode. """
    # all other scenes are parts of the story
    else:
        instructions = f"""Write a child appropriate script for a current scene where {current_scene_description} including some of the
        characters from {characters}. Characters traits should be revealed through context of action and dialogue. New characters must be
        introduced to the audience through the script. Here is what already happened in this episode {past_scene_descriptions}. Here is
        what will happen in the episode after this current scene you're writing now {future_scene_descriptions}. """

    dialogue = """Key for each line of dialogue must start with a 3 digit number starting with 001 and increasing for each line with the
    character name following. Characters names are all lower case and if their name is two words they should be separated by a space ' ' not '_'.
    Example '003steve smith' the name in the key for each line of dialogue must match the characer's name exactly. """
    sfx = """Sound effects should occur often and should be numbered in order along with dialogue, the number should be followed by 'SFX'.
    For example, the key would be 005SFX. The value should be a simple general term with spaces instead of underscores, like 'cat meow',
    'water pouring', or 'cicadas'. """
    music = "The 'music' key should have a value with a simple searchable term for film score. example 'anxious film score'. "
    ambience = " The 'ambience' key should have a value with a simple searchable term for ambience. Example: 'beach ambience'. "
    format = f"Respond in this format {script_template_string}. Don't use the names here. Only use characters from {characters}. Don't add any new keys. "

    # final prompt
    prompt = instructions + dialogue + sfx + music + ambience + format
    # print(f"Prompt: {prompt}")

    while True:
        try:
            # send prompt to Chat GPT
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            # extract string from response
            response = completion.choices[0].message['content']
            try:
                # parse response to script
                script_dict = json.loads(response)

                # ensure all character names are lowercase
                script_dict = {key.lower(): value for key, value in script_dict.items()}

                # ensure all character names have ' ' instead of '_'
                script_dict = {key.replace('_', ' '): value for key, value in script_dict.items()}

            except json.JSONDecodeError as e:
                print("Error decoding JSON response:", e)
                print("Retrying request...")
                # print(response)     # comment in to print response that caused json parsing error for debugging
                continue

            if 'music' not in script_dict or 'ambience' not in script_dict:
                # If 'music' or 'ambience' keys are missing, resend the request to ChatGPT
                print("Music or ambience not selected. Retrying request...")
                continue

            # add newly generated script dict to series dict
            series_dict["seasons"][f"s{season_num}"]["episodes"][f"e{episode_num}"]["scenes"][f"sc{scene_num}"]["script"] = script_dict

            break  # Break out of the loop if the request is successful

        except (openai.error.RateLimitError, openai.error.Timeout):
            # If RateLimitError or Timeout occurs, wait for a short period and try again
            time.sleep(2)
            continue

    # make sure new voices are valid
    series_dict = check_voices(series_dict)

    # save series dict to json
    save_json(series_dict["series title"], series_dict)

    return series_dict

def generate_one_line_dialogue(series_dict: dict, season_num: int, episode_num: int, scene_num: int, key: str, dialogue: str):
    """Takes as input, series dict, scene num, character name key, dialogue. Synthesizes speech from dialogue and saves mp3 to disk."""

    # Extracts character names from dict by removing the digit number leader
    character = key[3:]
    # try assign voice characteristics to local variable and assign standard if does not exist
    try:
        char_voice = series_dict["characters"][character]["voice"]
        char_pitch = series_dict["characters"][character]["audioConfig"]["pitch"]
        char_rate = series_dict["characters"][character]["audioConfig"]["speakingRate"]
    except KeyError:
        # print(json.dumps(series_dict["characters"], indent=4))  # uncomment for debugging on key error
        valid_voice_names = [f'en-US-Neural2-{char}' for char in 'ACDEFGHIJ']
        series_dict["characters"][character] = {
                "description": "Mystery character.",
            "voice": {
                "languageCode": "en-US",
                "name": random.choice(valid_voice_names)
            },
            "audioConfig": {
                "pitch": random.uniform(-10.0, 10.0),
                "speakingRate": random.uniform(0.9, 1.1)
            }
        }
        char_voice = series_dict["characters"][character]["voice"]
        char_pitch = series_dict["characters"][character]["audioConfig"]["pitch"]
        char_rate = series_dict["characters"][character]["audioConfig"]["speakingRate"]
        # save series dict to json
        save_json(series_dict["series title"], series_dict)
    try:
        # create client object for tts
        client = texttospeech.TextToSpeechClient(credentials=google_credentials)
        # prepare text
        input_text = texttospeech.SynthesisInput(text=dialogue)
        # set voice characteristics
        voice = texttospeech.VoiceSelectionParams(
            language_code=char_voice["languageCode"],
            name=char_voice["name"],
        )
    
        # audio encoding settings
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            pitch = char_pitch,
            speaking_rate = char_rate
        )
        # make API call to google using client object and assign audio file to response
        response = client.synthesize_speech(
            request={"input": input_text, "voice": voice, "audio_config": audio_config}
        )
        # create path name to directory and create dir if it doesn't exist
        dir = os.path.join(series_dict["series title"], f"s{season_num}", f"e{episode_num}", f"sc{scene_num}","01_tracks_dial_sfx")
        os.makedirs(dir, exist_ok=True)

        # create path for file to save
        file_path = os.path.join(dir, key + ".mp3")

        # save the audio file 
        with open(file_path, "wb") as out:
            out.write(response.audio_content)
            print(f'Audio content written to file "{file_path}"')
    except Exception as e:
        print('An error occurred:', str(e))
    return series_dict

def generate_one_sfx(series_dict: dict, season_num: int, episode_num: int, scene_num: int, key: str, effect: str):
    """Takes as input, series dict, scene num, effect number, description. Creates sfx audio and saves mp3 to disk."""

    # create client object from freesound.org and set API credentials
    client = freesound.FreesoundClient()
    client.set_token(SOUND_API_KEY, "token")

    # set parameters so earch for effects less than 3 seconds
    filter_params = {
        'query': effect,
        'fields': 'id,name,previews,duration',
        'filter': 'duration:[0 TO 3]'
    }

    # API call with keywork argument unpacking
    results = client.text_search(**filter_params)

    try:
        # select the first response
        sound = next(iter(results))

        # create filename from key number and audio filename
        file_name = f"{key}{sound}.mp3"

        # set directory path and creat if it doesn't exist
        dir = os.path.join(series_dict["series title"], f"s{season_num}", f"e{episode_num}", f"sc{scene_num}","01_tracks_dial_sfx")
        os.makedirs(dir, exist_ok=True)

        # create file path
        file_path = os.path.join(dir, file_name)

        # Save the sound file with the specified file name
        try:
            sound.retrieve_preview(dir, file_name)
            print(f'SFX saved to file "{file_path}"')
        except FileNotFoundError:
            # if no sounds were found in the search, then give up
            return

    except StopIteration:
        print("No search results found.")

def create_dialogue_sfx(series_dict: dict, season_num: int, episode_num: int, scene_num: int):
    """Takes as input series dict and scene number and saves all lines of dialoge and sound effects to project dir."""

    print(f"\n{'-' * 100}\n\nStep 4: Downloading dialogue from Google TTS and SFX from freesound.org for episode {episode_num} scene {scene_num}.\n")

    # alias for script dict
    script = series_dict["seasons"][f"s{season_num}"]["episodes"][f"e{episode_num}"]["scenes"][f"sc{scene_num}"]["script"]

    # local variable for scene audio file directory
    dir = os.path.join(series_dict["series title"], f"s{season_num}", f"e{episode_num}", f"sc{scene_num}", "01_tracks_dial_sfx")

    # Check if the audio file directory exists already exists from previous generation of this show
    if os.path.exists(dir):
        # delete all audio files in the directory
        for filename in os.listdir(dir):
            file_path = os.path.join(dir, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
    else:
        # create the directory if it doesn't exist
        os.makedirs(dir)

    # iterate over the keys and create audio files
    for key in script.keys():
        # check if item is sfx
        if 'sfx' in key or 'SFX' in key:
            # get effect description
            effect = script[key]
            # generate sfx audio file and save to dir
            generate_one_sfx(series_dict, season_num, episode_num, scene_num, key, effect)
        # check if item is dialogue
        elif key[0] == '0' in key:
            # get line dialogue
            dialogue = script[key]
            # generate dialogue audio file and save to dir
            generate_one_line_dialogue(series_dict, season_num, episode_num, scene_num, key, dialogue)

def combine_scene_audio(series_dict: dict, season_num: int, episode_num: int, scene_num: int):
    """Takes as input series dict and scene num. Combines dialogue and sounds effects from one scene into one sound file and saves it."""
    # local variable for individual dialogue and sfx file directory
    dir = os.path.join(series_dict["series title"], f"s{season_num}", f"e{episode_num}", f"sc{scene_num}","01_tracks_dial_sfx")
    # create the directory if it doesn't exist
    # os.makedirs(dir, exist_ok=True)

    # get a list of all audio files in the directory and put in numerical order
    audio_files = sorted([file for file in os.listdir(dir) if file.endswith('.mp3')])

    # create an empty AudioSegment object to store the combined audio
    combined_audio = AudioSegment.empty()

    print(f"\n{'-' * 100}\n\nStep 5: Combining scene audio.")

    # iterate over the all files in dir
    for file in audio_files:
        # reconstruct file path
        file_path = os.path.join(dir, file)
        try:
            # create audiosegment object for individual audio file
            audio_segment = AudioSegment.from_file(file_path, format='mp3')
        except:
            pass
            # if '$' in file:
            #     script = series_dict["seasons"]["season_num"]["episodes"]["episode_num"]["scenes"]["scene_num"]["script"]
            #     key = file.replace(".mp3", "")
            #     dialogue = script[key]
            #     generate_one_line_dialogue(series_dict, season_num, episode_num, scene_num, key, dialogue)
            #     audio_segment = AudioSegment.from_file(file_path, format='mp3')
        # concatenate individual audio object to combined scene audio object
        combined_audio += audio_segment

    # create scene dialogue and sound effects dir
    output_dir = os.path.join(series_dict["series title"], f"s{season_num}", f"e{episode_num}", f"sc{scene_num}", "02_scene_dial_sfx")
    os.makedirs(output_dir, exist_ok=True)

    # scene file path
    combined_scene_audio = f'{series_dict["series title"]} s{season_num}e{episode_num}sc{scene_num} combined audio'

    # file save path
    output_file = os.path.join(output_dir, f"{combined_scene_audio}.mp3")
    combined_audio.export(output_file, format='mp3')

    # convert scene audio length from milliseconds to seconds
    duration = len(combined_audio) / 1000.0
    print(f"Combined scene audio saved to dir /02_scene_dial_sfx/' with duration: {duration} seconds")

def get_music(series_dict: dict, season_num: int, episode_num: int, scene_num: int):
    """Takes as inputs series dict and scene number, downloads music, and saves audio file to dir"""
    # create scene music dir
    output_dir = os.path.join(series_dict["series title"], f"s{season_num}", f"e{episode_num}", f"sc{scene_num}", "03_music")
    os.makedirs(output_dir, exist_ok=True)

    # Delete all files in the directory if scene has been created before
    for file in os.listdir(output_dir):
        file_path = os.path.join(output_dir, file)
        if os.path.isfile(file_path):
            os.remove(file_path)

    print(f"\n{'-' * 100}\n\nStep 6: Downloading music from freesound.org for episode {episode_num} scene {scene_num}.")
    # get theme music for first and last scene
    if scene_num == 1 or scene_num == 10:
        score = series_dict["theme music"]
    # get sponsor music for sponsor scene
    elif scene_num == 6:
        score = series_dict["sponsor music"]
    # for story scenes get music based on scene music search term
    else:
        score = series_dict["seasons"][f"s{season_num}"]["episodes"][f"e{episode_num}"]["scenes"][f"sc{scene_num}"]["script"]["music"]

    # create client object for freesound.org and set API key
    client = freesound.FreesoundClient()
    client.set_token(SOUND_API_KEY, "token")
    # set search parameters
    filter_params = {
        'query': score,
        'fields': 'id,name,previews,duration',
    }
    # API call with keywork argument unpacking
    results = client.text_search(**filter_params)

    try:
        # get the first search result longer than 30 seconds
        sound = next((s for s in results if s.duration > 30))
        # create filename based on search term
        file_name = score + ".mp3"
        # Save the sound file with the specified file name
        sound.retrieve_preview(output_dir, file_name)
        print("Downloaded:", file_name)
    except StopIteration:
        print("No search results found.")

def add_music(series_dict: dict, season_num: int, episode_num: int, scene_num: int, norm_factor: int):
    """Inputs: series dict, scene number, norm factor (higher = quieter music), combines music with scene audio and saves to dir."""

    print(f"\n{'-' * 100}\n\nStep 7: Mixing music into scene for episode {episode_num} scene {scene_num}.")

    # local variable for convenience
    scene_dir = os.path.join(series_dict["series title"], f"s{season_num}", f"e{episode_num}", f"sc{scene_num}")

    # directory path
    dial_dir = os.path.join(scene_dir, "02_scene_dial_sfx")
    music_dir = os.path.join(scene_dir, "03_music")
    output_dir = os.path.join(scene_dir, "04_dial_music")
    os.makedirs(output_dir, exist_ok=True)

    # get the file names in the directories
    dial_files = [file for file in os.listdir(dial_dir) if file.endswith('.mp3')]
    music_files = [file for file in os.listdir(music_dir) if file.endswith('.mp3')]

    # check if there are files in the dial_dir
    if len(dial_files) == 0:
        print("Error: No dialogue file found.")
        return

    # Check if there are files in the music_dir
    if len(music_files) == 0:
        # only dial audio is present, use only that
        dial_file = os.path.join(dial_dir, dial_files[0])
        output_file = os.path.join(output_dir, dial_files[0])

        # load the audio file
        dial_audio = AudioSegment.from_file(dial_file)

        # export the dial audio as a new file
        dial_audio.export(output_file, format='mp3')
        print("Dialogue audio saved as:", output_file)
        return

    # Ensure there is only one mp3 file in each directory
    if len(dial_files) != 1 or len(music_files) != 1:
        print("Error: There should be only one mp3 file in each directory.")
        return

    # file paths to individual files
    dial_file = os.path.join(dial_dir, dial_files[0])
    music_file = os.path.join(music_dir, music_files[0])
    output_file = os.path.join(output_dir, dial_files[0].replace('.', '_music.'))

    # load audio files as audiosegment objects
    dial_audio = AudioSegment.from_file(dial_file)
    music_audio = AudioSegment.from_file(music_file)

    # repeat the music audio to match the length of the scene audio
    repeated_music_audio = music_audio * (len(dial_audio) // len(music_audio) + 1)
    # trim music length to match the scene audio length
    repeated_music_audio = repeated_music_audio[:len(dial_audio)]

    # apply fade-in and fade-out to the music audio
    faded_music_audio = repeated_music_audio.fade_in(1000).fade_out(1000)

    # minimum gain adjustment in dB
    min_gain = -20.0
    # maximum gain adjustment in dB
    max_gain = 0.0  
    # limit the norm_factor between 1 and 10
    norm_factor = max(min(norm_factor, 10), 1)
    # calculate the desired gain adjustment based on the norm_factor
    desired_gain = min_gain + (max_gain - min_gain) * ((norm_factor - 1) / 9)
    # apply the gain adjustment to the music audio
    adjusted_music_audio = faded_music_audio.apply_gain(desired_gain)

    # blend the scene audio and the adjusted music audio
    mixed_audio = dial_audio.overlay(adjusted_music_audio)
    # export the mixed audio as a new file
    mixed_audio.export(output_file, format='mp3')
    print("Mixed audio with dialogue and music saved to /04_dial_music/")

def get_simple_ambience(series_dict: dict, season_num: int, episode_num: int, scene_num: int):
    """Takes as inputs series dict and scene number, gets ambience sound file and saves to dir."""

    # create dir for ambience audio file
    output_dir = os.path.join(series_dict["series title"], f"s{season_num}", f"e{episode_num}", f"sc{scene_num}", "05_ambience")
    os.makedirs(output_dir, exist_ok=True)  # Create the directory if it doesn't exist

    # delete all files in the directory before downloading new music if scene has been generated before
    for file in os.listdir(output_dir):
        file_path = os.path.join(output_dir, file)
        if os.path.isfile(file_path):
            os.remove(file_path)

    # local variable for ambience search term
    ambience = series_dict["seasons"][f"s{season_num}"]["episodes"][f"e{episode_num}"]["scenes"][f"sc{scene_num}"]["script"]["ambience"]
    
    print(f"\n{'-' * 100}\n\nStep 8: Downloading ambience from freesound.org for episode {episode_num} scene {scene_num}.")

    # create client object for freesound.org and set API key
    client = freesound.FreesoundClient()
    client.set_token(SOUND_API_KEY, "token")
    # set search filter params
    filter_params = {
        'query': ambience,
        'fields': 'id,name,previews,duration',
    }
    # API call with keywork argument unpacking
    results = client.text_search(**filter_params)

    try:
        # Get the first search result longer than 30 seconds
        sound = next((s for s in results if s.duration > 30))
        file_name = ambience + ".mp3"
        # Save the sound file with the specified file name
        sound.retrieve_preview(output_dir, file_name)
        print("Downloaded:", file_name, "to /05_ambience/")
    except StopIteration:
        print("No search results found.")

def add_simple_ambience(series_dict: dict, season_num: int, episode_num: int, scene_num: int, norm_factor: int):
    """Inputs: series dict, scene number, norm factor (higher = quieter music), combines ambience with scene (with music) and saves to dir."""
    print(f"\n{'-' * 100}\n\nStep 9: Mixing ambience into scene for episode {episode_num} scene {scene_num}.")
    
    # scene dir
    scene_dir = os.path.join(series_dict["series title"], f"s{season_num}", f"e{episode_num}", f"sc{scene_num}")

    # directory paths
    input_dir = os.path.join(scene_dir, "04_dial_music")
    ambience_dir = os.path.join(scene_dir, "05_ambience")
    output_dir = os.path.join(scene_dir, "06_dial_music_ambience")
    os.makedirs(output_dir, exist_ok=True)

    # get the file names in the directories
    dial_files = [file for file in os.listdir(input_dir) if file.endswith('.mp3')]
    music_files = [file for file in os.listdir(ambience_dir) if file.endswith('.mp3')]

    # check if there are files in the input_dir
    if len(dial_files) == 0:
        print("Error: No input file found.")
        return

    # check if there are files in the ambience_dir
    if len(music_files) == 0:
        # if only input audio is present, pass it through
        input_file = os.path.join(input_dir, dial_files[0])
        output_file = os.path.join(output_dir, dial_files[0])

        # load the audio file
        input_audio = AudioSegment.from_file(input_file)

        # export the input audio as a new file
        input_audio.export(output_file, format='mp3')
        print("Output audio saved as:", output_file)
        return

    # ensure there is only one mp3 file in each directory
    if len(dial_files) != 1 or len(music_files) != 1:
        print("Error: There should be only one mp3 file in each directory.")
        return

    # individual file paths
    dial_file = os.path.join(input_dir, dial_files[0])
    music_file = os.path.join(ambience_dir, music_files[0])
    output_file = os.path.join(output_dir, dial_files[0].replace('.', '_ambience.'))

    # load the audio files objects
    dial_audio = AudioSegment.from_file(dial_file)
    ambience_audio = AudioSegment.from_file(music_file)

    # repeat the ambience audio to match the length of the scene audio
    repeated_ambience_audio = ambience_audio * (len(dial_audio) // len(ambience_audio) + 1)
    # trim ambience to match the scene audio length
    repeated_ambience_audio = repeated_ambience_audio[:len(dial_audio)]

    # Apply fade-in and fade-out to the music audio
    faded_ambience_audio = repeated_ambience_audio.fade_in(1000).fade_out(1000)

    # minimum gain adjustment in dB
    min_gain = -20.0
    # maximum gain adjustment in dB
    max_gain = 0.0
    # limit the norm_factor between 1 and 10
    norm_factor = max(min(norm_factor, 10), 1)
    # calculate the desired gain adjustment based on the norm_factor
    desired_gain = min_gain + (max_gain - min_gain) * ((norm_factor - 1) / 9)

    # Apply the gain adjustment to the music audio
    adjusted_ambience_audio = faded_ambience_audio.apply_gain(desired_gain)

    # Blend the scene audio and the adjusted music audio
    mixed_audio = dial_audio.overlay(adjusted_ambience_audio)

    # Export the mixed audio as a new file
    mixed_audio.export(output_file, format='mp3')
    print("Mixed audio with dialogue music and ambience saved to /06_dial_music_ambience/")

def combine_episode_audio(series_dict: dict, season_num: 1, episode_num: 1):
    """Takes as input series dict and episode number. Combines completed scene audio files into one episode file and saves to dir."""
    print(f"\n{'-' * 100}\n\nStep 10: Creating final episode audio.")
    
    # directory for this episode
    dir = os.path.join(series_dict["series title"], f"s{season_num}", f"e{episode_num}")

    # fet a list of all scene directories starting with 'sc' and sort them numerically starting at index 2 (scene number)
    scene_dirs = sorted([file for file in os.listdir(dir) if file.startswith('sc')], key=lambda x: int(x[2:]))

    # check how many scenes were created out of 10
    num_scenes = len(scene_dirs)

    # create an empty AudioSegment object to store the combined audio
    combined_audio = AudioSegment.empty()

    # iterate over the scene directories
    for scene_dir in scene_dirs:
        # directory were each completed scene audio file is saved
        dial_music_dir = os.path.join(dir, scene_dir, "06_dial_music_ambience")
        # get the completed scene audio file
        audio_files = [file for file in os.listdir(dial_music_dir) if file.endswith('.mp3')]
        # skip scene if there is no audio file or multiple audio files in the directory
        if len(audio_files) != 1:
            continue
        # create file path to save combined episode    
        file_path = os.path.join(dial_music_dir, audio_files[0])
        audio_segment = AudioSegment.from_file(file_path, format='mp3')
        combined_audio += audio_segment

    # create dir to save completed episode audio
    output_dir = os.path.join(series_dict["series title"], "output")
    os.makedirs(output_dir, exist_ok=True)

    # create audio file name
    combined_episode_audio = f'{series_dict["series title"]} s{season_num}e{episode_num}'
    if num_scenes != 10:
        suffix = f' scenes {num_scenes} of 10'
        combined_episode_audio += suffix

    # create file save path
    output_file = os.path.join(output_dir, f"{combined_episode_audio}.mp3")
    print(output_file)
    combined_audio.export(output_file, format='mp3')

    # convert length in milliseconds to seconds
    duration_seconds = len(combined_audio) / 1000.0
    duration = f'{int(duration_seconds // 60)}:{str(int(duration_seconds % 60)).zfill(2)}'

    episode_title = series_dict["seasons"][f"s{season_num}"]["episodes"][f"e{episode_num}"]["episode title"]

    print("\n", "=" * 100, "\n")

    if num_scenes == 10:
        print(f"Episode {episode_num}: {episode_title} created successfully and saved to /Output/ with duration {duration}")
    else:
        print(f"{num_scenes}/10 scenes of episode {episode_num}: {episode_title} created and saved to /Output/ with duration: {duration}")
    print(f"\nThank you for using SeriesGPT!\n")
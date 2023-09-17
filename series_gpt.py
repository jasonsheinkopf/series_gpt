import os
import openai
from helper_functions import *
from dotenv import load_dotenv
import time

# load secret keys from .env file
load_dotenv()

# load environmental varIables from .env file
SOUND_API_KEY = os.getenv("SOUND_API_KEY")
openai.api_key = os.getenv("OPEN_AI_API_KEY")

def create_scenes_with_checkpoints(series_description: str, sponsor: str, series_title:str, num_scenes: int=1):
    """
    Use this function to step through the process for 1 or more scenes of one episode. A full season outline is
    always created first. Takes series description, sponsor, title and number of scenes as arguments.
    Number of scenes should be [1, 10]. After each step, check for errors and press <enter> to continue.
    """

    # start function timer
    start_time = time.time()

    # Step 1: generate season 1 outline and check if properly created
    series_dict = generate_season_outline(series_description, sponsor, season=1, series_title=series_title)
    print(json.dumps(series_dict, indent=4))
    print(f"\n* Check that /{series_title}/ directory with show .json was created.")
    input(f"* Dictionary printout above should includes: character descriptions and a 10 episode season outline. <enter>")

    """
    if you want to call some of these function after season outline has been created for a show, uncomment the line below
    and modify the string to match your show name. Then you can comment out steps 1-9.
    """
    # series_dict = load_series_dict(series_title) # uncomment for debugging only

    # Step 2: create episode outline and add to series_dict and check if episode outline was properly created
    series_dict = generate_episode_outline(series_dict, season_num=1, episode_num=1)
    print(json.dumps(series_dict["seasons"]["s1"]["episodes"]["e1"], indent=4))
    input("\n* Check that the printout above has an scene description for all 10 scenes. <enter>")

    # Step 3: generate scene scripts and check if properly created
    for scene in range(1, num_scenes + 1):
        series_dict = generate_scene_script(series_dict, season_num=1, episode_num=1, scene_num=scene)
    print(json.dumps(series_dict["seasons"]["s1"]["episodes"]["e1"]["scenes"], indent=4))
    input("\n* Check that the printout above has a script for each scene requested. <enter>")

    # Step 4: create audio for scene(s)
    for scene in range(1, num_scenes + 1):
        create_dialogue_sfx(series_dict, season_num=1, episode_num=1, scene_num=scene)
    input("\n* Check project dir and make sure each scene's /01_tracks_dial_sfx/ dir contains dialogue and SFX audio files then press <enter>.")

    # Step 5: create combined audio for scene(s)
    for scene in range(1, num_scenes + 1):
        combine_scene_audio(series_dict, season_num=1, episode_num=1, scene_num=scene)
    input("\n* Check project dir and make sure each scene's /02_scene_dial_sfx/ dir contains one combined audio file then press <enter>.")

    # Step 6: get music for scene(s)
    for scene in range(1, num_scenes + 1):
        get_music(series_dict, season_num=1, episode_num=1, scene_num=scene)
    input("\n* Check project dir and make sure each scene's /03_music/ dir contains one music audio file then press <enter>.")

    # Step 7: add music to scene(s)
    for scene in range(1, num_scenes + 1):
        add_music(series_dict, season_num=1, episode_num=1, scene_num=scene, norm_factor=1)
    input("\n* Check project dir and make sure each scene's /04_dial_music/ dir contains one audio file then press <enter>.")

    # Step 8: get simple ambience for scene(s)
    for scene in range(1, num_scenes + 1):
        get_simple_ambience(series_dict, season_num=1, episode_num=1, scene_num=scene)
    input("\n* Check project dir and make sure each scene's /05_ambience/ contains one ambience audio file then press <enter>.")

    # Step 9: add simple ambience
    for scene in range(1, num_scenes + 1):
        add_simple_ambience(series_dict, season_num=1, episode_num=1, scene_num=scene, norm_factor=1)
    input("\n* Check project dir and make sure each scene's /06_dial_music_ambience/ dir contains one audio file then press <enter>.")

    # Step 10: assemble episode(s)
    combine_episode_audio(series_dict, season_num=1, episode_num=1)

    # end timer
    end_time = time.time()

    # calculate how long function took to run
    execution_time = end_time - start_time
    execution_minutes = int(execution_time // 60)
    execution_seconds = int(execution_time % 60)
    execution_time_formatted = f"{execution_minutes} minutes and {execution_seconds:02} seconds"
    print(f"{num_scenes}/10 scenes of episode 1 were created in {execution_time_formatted}")

def create_full_episodes(series_description: str, sponsor: str, series_title: str, num_episodes: int):
    """Takes series description, sponsor, title and number of episodes as arguments. Number of episodes should be [1, 10]."""
    
    # start timer
    start_time = time.time()

    # create season 1 outline
    series_dict = generate_season_outline(series_description, sponsor, season=1, series_title=series_title)
    
    # series_dict = load_series_dict(series_title) # uncomment for debugging only

    for episode in range(1, num_episodes + 1):
        # create episode outline
        series_dict = generate_episode_outline(series_dict, season_num=1, episode_num=episode)
        # create one episode
        for scene in range(1, 11):
            # create scene scripts
            series_dict = generate_scene_script(series_dict, season_num=1, episode_num=episode, scene_num=scene)

            # episode individual dialogue tracks
            create_dialogue_sfx(series_dict, season_num=1, episode_num=episode, scene_num=scene)

            # create episode scene audio with dialogue and sfx
            combine_scene_audio(series_dict, season_num=1, episode_num=episode, scene_num=scene)

            # get music for episode
            get_music(series_dict, season_num=1, episode_num=episode, scene_num=scene)

            # add music to episode
            add_music(series_dict, 1, episode, scene, 1)

            # get simple ambience for episode
            get_simple_ambience(series_dict, season_num=1, episode_num=episode, scene_num=scene)

            # add music to episode
            add_simple_ambience(series_dict, 1, episode, scene, 1)

        # create combined episode
        combine_episode_audio(series_dict, season_num=1, episode_num=episode)

    # end timer
    end_time = time.time()

    # calculate how long function took to run
    execution_time = end_time - start_time
    execution_minutes = int(execution_time // 60)
    execution_seconds = int(execution_time % 60)
    execution_time_formatted = f"{execution_minutes:02} minutes and {execution_seconds:02} seconds"
    print(f"{num_episodes} episodes were created in {execution_time_formatted}")

################################################################################################################

# series_description = """
# A ridiculous comedy thriller where a supergenius gnat named Gnathan becomes the leader of all other gnats
# and uses his power to achieve a goal of slightly annoying people in the summer. His idea is that if he distracts
# all of humanity just a little bit, then the chimpanzees will have an advantage and take over the world. He
# wants this to happen because chimpanzees don't put their food in the refrigerator and it will we easier to lay
# eggs in it. Even though he's the villain, the audience likes him because his cause is relatable. 
# A garbage man named Squish Jones catches on to Gnathan's plan and tries to stop him.
# 
# """

# series_title = "Gnat Your Average Supervillain"
# sponsor = "Acme Trash Compactors"

################################################################################################################

series_title = "Strike While the Iron's Bot"
sponsor = "General Refrigerant 134a"

series_description = """
A washing machine gets struck by lightning and becomes a self-aware robot named Spinner. Since there are no others
like him, he creates a technology that starts lightning storms near appliance stores in the hopes that more like
him will be created. A refrigerator store owner named Mr. Freeze discovers his plan and tries to convince the
government of Spinner's plan and to stop him, but President Chip doesn't believe him. Eventually, Spinner's plan
works and an army of dim-witted robots are spawned by the lightning. The story follows their journey as they try to
integrate into modern society.
"""

################################################################################################################

# series_title = "Ancient Aliens: Thomas Edison"
# sponsor = "Zap Waterproof Lightbulbs"

# series_description = """
# A telling of the life of Thomas Edison that mostly follows the actual events of his life but also includes how
# most of his inventions were developed by reverse engineering alien technology found in the pyramids. It should
# feature the actual people in his life and also an alien named Gortinazoopie who only Edison can see and always
# gets Edison in trouble by suggesting bad invention ideas as a joke. Gortinazoopie thinks it's funny when nobody
# likes Edison's bad inventions.
# """

################################################################################################################

# series_title = "your show title here"
# sponsor = "your sponsor here"

# series_description = """
# put your series description here
# """

################################################################################################################

"""
How to use SeriesGPT:
1. Write your series information above.
2. Create .env and google_auth.json file with your personal keys
3. Run file with create_full_episodes
4. Completed audio files found in show directory/output
5. Try create_scenes_with_checkpoints() to step through the proces
"""

# create_scenes_with_checkpoints(series_description, sponsor, series_title, num_scenes=2) # steps through creation of scene(s) [1, 10]

create_full_episodes(series_description, sponsor, series_title, num_episodes=10) # creates full episode(s) [1, 10]
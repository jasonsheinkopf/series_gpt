<a href="https://www.buymeacoffee.com/jasonsheinkopf" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>

# Series GPT
This program uses ChatGPT, Google Text-to-Speech, and Freesound.org to create full ~15min serialized podcast episodes from a short prompt.
- input a title, few sentence prompt, and sponsor
- an audio file is created with voiced characters, sound effects, music, and ambience
- create up to a full 10-episode season in one click

# Podcasts Created with Series GPT
### ["Ancient Aliens: Thomas Edison" sponsored by Zap Waterproof Lightbulbs.](https://on.soundcloud.com/N6ULZ)

<img src="https://github.com/jasonsheinkopf/series_gpt/blob/c3496efa40fd5a4ab2dc148603f74e5026aca252/Ancient%20Aliens%3A%20Thomas%20Edison/output/Ancient%20Aliens%20Thomas%20Edison.png" width="200" height="200">    

A telling of the life of Thomas Edison that mostly follows the actual events of his life but also includes how most of his inventions were developed by reverse engineering alien technology found in the pyramids. It should feature the actual people in his life and also an alien named Gortinazoopie who only Edison can see and always gets Edison in trouble by suggesting bad invention ideas as a joke. Gortinazoopie thinks it's funny when nobody likes Edison's bad inventions.  
### ["Strike While the Iron's Bot" sponsored by General Refrigerant 134a](https://on.soundcloud.com/jZ4vx)

<img src="https://github.com/jasonsheinkopf/series_gpt/blob/c3496efa40fd5a4ab2dc148603f74e5026aca252/Strike%20While%20the%20Iron's%20Bot/output/Strike%20While%20the%20Iron's%20Bot%20Show%20Icon.png" width="200" height="200">  

A washing machine gets struck by lightning and becomes a self-aware robot named Spinner. Since there are no others
like him, he creates a technology that starts lightning storms near appliance stores in the hopes that more like
him will be created. A refrigerator store owner named Mr. Freeze discovers his plan and tries to convince the
government of Spinner's plan and to stop him, but President Chip doesn't believe him. Eventually, Spinner's plan
works and an army of dim-witted robots are spawned by the lightning. The story follows their journey as they try to
integrate into modern society.  

# Installation
## 1. Clone the Repository
```bash
git clone [https://github.com/jasonsheinkopf/youtube_stat_counter.git](https://github.com/jasonsheinkopf/series_gpt.git)
```
## 2. Create virtual environment from .yml
```bash
conda env create -f environment.yml
```
## 3. Activate virtual environment
```base
conda activate series_gpt
```
## 4. Authorize Open AI and Freesound
Create new file named .env in root directory, add these lines of code  
```OPEN_AI_API_KEY = 'OPEN_AI_API_KEY'``` ```SOUND_API_KEY = 'SOUND_API_KEY'```
Replace strings with your info.  
[How to get an OpenAI API key](https://platform.openai.com/account/api-keys)  
[How to get a Freesound API key](https://freesound.org/help/developers/#:~:text=In%20order%20to%20use%20the,(Freesound%20login%20is%20required))
## 5. Authorize Google TTS
Make a Google Workspace account and create google_auth.json.
[How to create google_auth.json](https://developers.google.com/workspace/guides/create-credentials)  
Your google_auth.json file should look like this.
```
{
  "type": "service_account",
  "project_id": "your info here",
  "private_key_id": "your info here",
  "private_key": "-----BEGIN PRIVATE KEY-----\nyour info here\n-----END PRIVATE KEY-----\n",
  "client_email": "your info here",
  "client_id": "your info here",
  "auth_uri": "your info here",
  "token_uri": "your info here",
  "auth_provider_x509_cert_url": "your info here",
  "client_x509_cert_url": "your info here",
  "universe_domain": "googleapis.com"
}
```

# How to Use Series GPT
#### Step 1. Open series_gpt.py
#### Step 2. Fill in series_title, sponsor, and series_description
#### Step 3. Run create_full_episode (change num_episodoes to create up to 10 episodes at once)
#### Step 4. Also, try create_scenes_with_checkpoints to step through creating one scene

# How it Works
## Step 1. Generate season outline
#### Create a prompt chain including:
- user input show information
- instructions
- example of expected formatted dictionary response
- Google TTS voice options
#### Send prompt to ChatGPT
#### Try to parse response to JSON and resend request if it fails
#### Save series_dict as JSON file

## Step 2. Generate episode outline
#### Create a prompt chain including:
- episode title, description, and character descriptions from series_dict
- instructions
- example of expected formatted dictionary response
#### Send prompt to ChatGPT
#### Try to parse response to JSON and resend request if it fails

## Step 3. Generate scene scripts
#### Create a prompt chain for each of 10 scenes including:
- scene description, past scene descriptions, future scene descriptions, 
- instructions
- example of expected formatted dictionary response
- whether the scene is intro, commerical, story, or outro
#### Send prompt to ChatGPT
#### Try to parse response to JSON and resend request if it fails
#### Check that voice types selected for Google TTS are valid and correct if necessary

## Step 4. Create Dialogue and SFX
#### Send each line of dialogue or sound effec to freesound.org API and save .mp3 to scene directory

## Step 5. Combine scene audio and save to scene directory

## Step 6-9. Download and mix music and ambience
#### Send scene music and ambience description to freesound.org API, mix, save to scene directory, and mix with scene audio.

## Step 10. Combine scene audio to one file and save

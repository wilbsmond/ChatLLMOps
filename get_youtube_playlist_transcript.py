import json
import os
import re
import requests
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled

def get_video_metadata_from_playlist(playlist_url):
    response = requests.get(playlist_url)
    html_content = response.text

    video_ids = []

    # Find the script tag that contains the JSON data
    script_tag = re.search(r'var ytInitialData = ({.*?});', html_content)

    # Dictionary to hold all video information
    playlist_dict = []

    if script_tag:
        # Parse the JSON data
        json_data = json.loads(script_tag.group(1))

        # Navigate through the JSON to extract video details
        # The keys and structure depend on the actual JSON provided by YouTube
        videos = json_data['contents']['twoColumnBrowseResultsRenderer']['tabs'][0]['tabRenderer']['content']['sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents'][0]['playlistVideoListRenderer']['contents']
        for video in videos:
            video_data = video['playlistVideoRenderer']
            video_metadata = {
                'title': video_data['title']['runs'][0]['text'],
                'video_id': video_data['videoId'],
                'video_url': f"https://www.youtube.com/watch?v={video_data['videoId']}",
                'length': video_data.get('lengthText', {}).get('simpleText', '')
            }
            playlist_dict.append(video_metadata)

    return playlist_dict

def get_transcript(playlist_dict):
    # Extract video_ids
    video_ids = [video['video_id'] for video in playlist_dict]

    # Get transcripts for all videos
    videos_transcript = []
    for video_id in video_ids:
        try:
            transcript_chunks = YouTubeTranscriptApi.get_transcript(video_id)
            # Parse transcript
            transcript = ' '.join(chunk["text"] for chunk in transcript_chunks)
            videos_transcript.append(transcript)
        except TranscriptsDisabled:
            print(f"Transcript disabled for video ID: {video_id}. Skipping.")
            videos_transcript.append("Transcript not available")

    print('# Transcripts: ', len(videos_transcript))

    # Check if the number of transcripts matches the number of videos
    if len(videos_transcript) != len(playlist_dict):
        raise ValueError("The number of transcripts does not match the number of videos")

    # Add transcripts to the videos
    for video, transcript in zip(playlist_dict, videos_transcript):
      video['transcript'] = transcript

    return playlist_dict

def sanitize_filename(filename):
    """
    Sanitize the filename by removing or replacing characters that are not allowed in file names.
    """
    return re.sub(r'[\\/*?:"<>|]', "", filename)

def save_playlist_transcript_as_txt(playlist_dict, subfolder):
  # Directory to save the transcript files (change as needed)
  save_directory = f'transcripts/{subfolder}'

  # Create the directory if it doesn't exist
  if not os.path.exists(save_directory):
      os.makedirs(save_directory)

  # Loop through each video and save its transcript in a separate text file
  for video in playlist_dict:
      filename = sanitize_filename(video['title']) + '.txt'
      file_path = os.path.join(save_directory, filename)

      with open(file_path, 'w', encoding='utf-8') as file:
          file.write(video['transcript'])

      print(f"Transcript saved: {file_path}")

if __name__ == "__main__":
  list_of_playlists = [
      "https://www.youtube.com/playlist?list=PL3vkEKxWd-us5YvvuvYkjP_QGlgUq3tpA",
      "https://www.youtube.com/playlist?list=PL3vkEKxWd-uupBSWL-DbVJuCMqXO9Z3Z4",
      "https://www.youtube.com/playlist?list=PL3vkEKxWd-usFkc3977ZeexYXS3GgDVSO"
  ]

  for i, playlist_url in enumerate(list_of_playlists):
    print(f"Transcripting playlist: {playlist_url}")
    playlist_dict = get_video_metadata_from_playlist(playlist_url)
    playlist_dict = get_transcript(playlist_dict)
    save_playlist_transcript_as_txt(playlist_dict, i)
#!/usr/bin/python3
import youtube_dl as yd
import os, requests, eyed3, selenium, gig, spotify_search, sys
from bs4 import BeautifulSoup
from sys import argv
from google_images_download import google_images_download

class YouDown(object):

    def __init__(self):

        self.music_dest = os.environ['HOME'] + '/Music/'
        self.google_img_query = "https://www.google.com/search?tbm=isch&q="

        self.yd_opts = {
            "outtmpl": self.music_dest + "%(title)s.%(ext)s",
            "format": "bestaudio/best",
            "postprocessors": [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        }

    def download_youtube_song(self, you_url):

        youtube_song_info = self.find_youtube_song(you_url)
        
        sp_srch = spotify_search.Spotify_Search()

        #print(youtube_song_info)

        youtube_audio_info = self.download_youtube_audio(you_url)

        target_num = None

        if all(value for value in youtube_song_info.values()):

            self.youdown_debug_print("Searching the RIGHT Way!")

            song_name = youtube_song_info['song']
            song_artist = youtube_song_info['artist']

            artwork_hosts = self.download_artwork("%s - %s spotify" % (song_name, song_artist)) # get artwork

            for index, host in enumerate(artwork_hosts):

                if self.check_image_uri(host):

                    target_num = index
                    break
            
            youdown_artwork_dir = self.find_image_path("%s - %s spotify" % (song_name, song_artist))

        else:
            
            artwork_hosts = self.download_artwork(youtube_audio_info.get('title', None) + " spotify") # get artwork
        
            #import pdb; pdb.set_trace()

            for index, host in enumerate(artwork_hosts):

                if not self.check_image_uri(host):

                    target_num = index
                    break

            youdown_artwork_dir = self.find_image_path(youtube_audio_info.get('title', None) + ' spotify')
        
        #import pdb; pdb.set_trace()

        if target_num == None:

            target_num = 0
        
        image_name = [f for d, s, f in os.walk(youdown_artwork_dir)][0][target_num]

        if youtube_song_info['song']:
            song_title = youtube_song_info['song']

        else:
            song_title = youtube_audio_info.get('title', None)       

        song_info = sp_srch.find_song_info(artwork_hosts[target_num], song_title)
        
        song_info['artwork_location'] = ("%s/%s" % (youdown_artwork_dir, image_name))

        #import pdb; pdb.set_trace()

        os.rename((os.environ['HOME'] + '/Music/') + str(youtube_audio_info.get('title', None)).replace(":", "_").replace("\"", "'") + '.mp3', os.environ['HOME'] + '/Music/' + song_info['song_name'] + '.mp3')

        #song_info['song_location'] = (os.environ['HOME'] + '/Music/') + youtube_audio_info.get('title', None) + '.mp3'

        song_info['song_location'] = (os.environ['HOME'] + '/Music/' + song_info['song_name'] + '.mp3')

        self.user_song_check(song_info)

        self.format_youtube_song(song_info)

    def user_song_check(self, song_info):

        self.youdown_debug_print("Song Name: %s" % (song_info['song_name']))
        self.youdown_debug_print("Artist Name: %s" % (song_info['artist_name']))
        self.youdown_debug_print("Album Name: %s" % (song_info['album_name']))

        usr_correct = self.query_yes_no("Is This Correct?")

    def query_yes_no(self, question, default="yes"):
        """Ask a yes/no question via raw_input() and return their answer.

        "question" is a string that is presented to the user.
        "default" is the presumed answer if the user just hits <Enter>.
            It must be "yes" (the default), "no" or None (meaning
            an answer is required of the user).

        The "answer" return value is True for "yes" or False for "no".
        """
        valid = {"yes": True,"y": True, "ye": True,
                "no": False, "n": False}
        if default is None:
            prompt = " [y/n] "
        elif default == "yes":
            prompt = " [Y/n] "
        elif default == "no":
            prompt = " [y/N] "
        else:
            raise ValueError("invalid default answer: '%s'" % default)

        while True:
            sys.stdout.write(question + prompt)
            choice = input().lower()
            if default is not None and choice == '':
                return valid[default]
            elif choice in valid:
                return valid[choice]
            else:
                sys.stdout.write("Please respond with 'yes' or 'no' "
                                "(or 'y' or 'n').\n")

    def find_youtube_song(self, you_url):

        youtube_song_info = {
            "song": None,
            "artist": None,
        }

        self.youdown_debug_print("Trying to find name of song...")

        you_resp = requests.get(you_url)
        
        you_soup = BeautifulSoup(you_resp.text, 'html.parser')
        
        if you_soup.find("div", {"id": "watch-description-extras"}):

            self.youdown_debug_print("Found Description Extras...")

            you_extras = you_soup.find("div", {"id": "watch-description-extras"})
            you_titles = you_soup.find_all("h4", {"class": "title"})
            you_unlists = you_extras.find_all("ul")

            for index, title in enumerate(you_titles):
                
                format_title = str(title.getText()).strip()
                
                if(format_title in ["Song", "Artist"]):

                    #print(you_unlists[index + 1])
                    self.youdown_debug_print("%s Categorey Found" % (format_title))
                    youtube_song_info[format_title.lower()] = you_unlists[index + 1].getText().strip()
        
        return youtube_song_info

    def format_youtube_song(self, song_info):

        artwork_data = open(song_info['artwork_location'], "rb").read()

        audio_file = eyed3.load(song_info['song_location'])
        audio_file.tag.artist = song_info['artist_name'] 
        audio_file.tag.album = song_info['album_name']
        audio_file.tag.title = song_info['song_name']
        audio_file.tag.release_date = song_info['release_date']
        audio_file.tag.images.set(3, artwork_data, 'image/jpeg')
        audio_file.tag.save()

    def find_image_path(self, search_query):

        download_directory = os.environ['PWD'] + '/downloads/'

        downloaded_queries = [(d, s, f) for d, s, f in os.walk(download_directory)]

        downloads_subdirs = downloaded_queries[0][1]
        
        downloaded_artwork_dir = [(download_directory + search_query) if search_query in downloads_subdirs else None]

        return downloaded_artwork_dir[0]

    def check_image_uri(self, image_url):

        print(image_url)

        if "open.spotify.com" in image_url:

            self.youdown_debug_print("Found Spotify source link")
            return True

        else:
            return False

    def download_youtube_audio(self, url):

        with yd.YoutubeDL(self.yd_opts) as yt_down:
            yt_down.download([url]);
            info_dict = yt_down.extract_info(url,download=False)

        return info_dict

    def download_artwork(self, search_query):

        image_grabber = gig.GoogleImageGrabber()
        sp_srch = spotify_search.Spotify_Search()
        #passing the arguments to the function
        #arguments = {"keywords":search_query,"limit":3, "print_urls":True}   #creating list of arguments  
        image_hosts = image_grabber.download_images(search_query, 3, True)

        return image_hosts

        #self.find_downloaded_image(search_query)

        #song_info = sp_srch.find_song_info(image_hosts[0])
    
        #return song_info

    def youdown_debug_print(self, debug_str):

        print("[YouDown] {}".format(str(debug_str)))

if __name__ == '__main__':

    target_url = argv[1]

    youdown = YouDown()

    youdown.download_youtube_song(target_url)

    #video_info = youdown.download_audio(target_url)

    #youdown.download_artwork(video_info.get('title', None)) # get artwork\
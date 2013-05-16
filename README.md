tabby-dances
============

a python script to stream music from GrooveShark by twitting command

### Usage
1. Install required dependencies
2. Fill in the key and secrete of your twitter app as well as user token
3. Change file paths
3. Write a tweet as `"@user play <song/artist name>"`

### Dependencies
Here are the libraries and programs used, use `pip` to install 

    $ pip install -r requirements.txt
    $ sudo apt-get install mpg123

- [`mpg123`](http://www.mpg123.de/) - version 1.15.1
- [`tweepy`](https://github.com/hezhao/tweepy) - my fork on tweepy which handles SSLError to remove crashes
- [`groove-dl`](https://github.com/jacktheripper51/groove-dl) - modified version, already included in source code


### License
BSD License


### Disclaimer
THIS SOFTWARE IS PROVIDED FOR PROOF OF CONCEPT PURPOSE ONLY. BY CONCEPT I MEAN ONE IS ABLE TO STREAM MUSIC FROM 
GROOVESHARK BY COMPOSING A MESSAGE ON TWITTER. I CANNOT BE HELD RESPONSIBLE FOR ANYTHING YOU DO WITH THE SOFTWARE
OR ANY CONSEQUENCES THEREOF. I DO NOT CONDONE COPYRIGHT INFRINGEMENT OR ANY OTHER ACTIVITIES WHICH VIOLATE
GROOVESHARK'S TERMS OF SERVICES.

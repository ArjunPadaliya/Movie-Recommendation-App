# Movie-Recommendation-App
A movie recommendation app made in Django framework of Python using the Movielens dataset. It's a stable dataset with 20 million ratings and 465,000 tag applications applied to 27,000 movies by 138,000 users. This dataset also includes, tag genome data with 12 million relevance scores across 1,100 tags. Data has been divided into six different files, genome-scores.csv, genome-tags.csv, links.csv, movies.csv, ratings.csv and tags.csv.

# Set-Up/Installation

1. Create Virtual Environment.

2. Within your virtual environment you will need to install all the packages that are within the requirements.txt to run the code base locally:
> Run from your terminal-
> **$ pip3 install -r requirements.txt**

> Check for errors
> **$ python3 manage.py check**

> Migrate the database
> - **$ python3 manage.py makemigrations**
> - **$ python3 manage.py migrate**

# Setting up Database

### Building the database yourself

1. Download the dataset manually from [here](http://files.grouplens.org/datasets/movielens/ml-20m.zip) and then download youtube links from [here](http://files.grouplens.org/datasets/movielens/ml-20m-youtube.zip). Extract both the files in the project folder.

2. Run the setup script run.py from the project's root directory to populate the local database by running the following command:
> **$ python3 run.py -i /extracted/dataset**

### Downloading the dataset

Run the setup script run.py from the project's root directory, this will download the dataset from the grouplens website, extract the dataset and will aslo populate the local database.This entire process is done by running just one command:
> **$ python3 run.py**

This process takes about 3 hours on my computer and the database amounts to be about little more than 6GB.

### Starting the server

Run the following command to start the server:
> **$ python3 manage.py runserver**

Open the server in any of the browser, by default it's running on IP 127.0.0.1:8000. Enjoy the app!

### Using the App

Homepage of the app displays 20 randomly picked movies for you, this excludes movies you have already rated and everytime list changes on refreshing the page. User can search for the movie using the search bar or user can select one from the homepage, this will bring them to the movie detail page where user can provide their feedback for that movie. Once, the database has enough feeback from the user, Recommendations page can recommend movies for you based on the likes and dislikes of the user.


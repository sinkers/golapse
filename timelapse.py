# Selection of functions for creating the timelapses

FFMPEG = "ffmpeg"

def get_day_images(day):
    # Get a list of all images for a given day
    # Will need to traverse all the hour dirs for a day and create an ordered list


def create_symlinks(file_list):
    # creates a set of symlinks to actual files to pass into ffmpeg to create the movie


def day_to_archive(day):
    # Takes a day worth of videos and converts these into a compressed movie format
    # Note that storing each full frame image is quite inefficient as there isn't a lot of change

def create_timelapse(file_list):
    # Create the timelapse
# golapse
Simple timelapse recorder for a gopro camera designed to run on a small Raspberry Pi or equivalent machine with 2 NICs so that it can connect to the GoPro which has closed wifi and also to an external network.

The whole setup has been built to run off a solar powered rig so can be placed remotely and is weather proof.

Features include
* Take a photo every x seconds
* Retrieves the photo from the gopro
* Store the photos to a local file server order by year/month/day/hour/seconds
* Detects a level of black in the photo so doesn't store night time photos
* Upload the latest photo to S3 so it can be served out to the web

Upcoming features
* Convert previous period photos to a video timelapse
* Upload timelapse videos
* Archive old footage as a more efficient h265 or VP9 given change between images is mostly low

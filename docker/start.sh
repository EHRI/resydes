#!/bin/bash --
# start.sh
#
# Start a Docker container with the Resydes application.
#
# Resydes is an implementation of a destination as described in
# http://www.openarchives.org/rs/1.0/resourcesync
#
# Usage:                ./start.sh [options]
# See help on options:  ./start.sh -h
# Run once and quit:    ./start.sh -o
#
# ############# THIS FILE SHOULD BE RUN IN A DOCKER TERMINAL ##################

###############################################################################
# Set variables to reflect current conditions
#
# The configuration directory.
CONFIG_DIR=$PWD/conf

# The directory for logs
LOG_DIR=$PWD/logs

# The destination directory
DESTINATION_DIR=$PWD/destination
###############################################################################

docker run -it --rm --name resydes \
    -v $CONFIG_DIR:/conf \
    -v $LOG_DIR:/logs \
    -v $DESTINATION_DIR:/destination \
    bhenk/resydes "$@"

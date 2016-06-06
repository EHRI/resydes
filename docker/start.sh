#!/bin/bash --

docker run -it --rm --name resydes \
    -v $PWD/resydes/logs:/logs \
    -v $PWD/resydes/destination:/destination \
    resydes
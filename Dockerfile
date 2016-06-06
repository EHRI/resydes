# Dockerfile
#
# Build the Resydes application.
#
FROM bhenk/resync

MAINTAINER henk.van.den.berg at dans.knaw.nl

COPY des /work/des/
COPY setup.py /work/
RUN pip install /work

RUN rm -R /work && \
    mkdir -p /conf && \
    mkdir -p /logs && \
    mkdir -p /destination
COPY docker/conf /conf/
COPY docker/startrunner.py /

VOLUME  /conf \
        /logs \
        /destination

ENTRYPOINT [ "python", "./startrunner.py" ]


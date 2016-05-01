# resydes

Destination harvester for [Resource Sync](http://www.openarchives.org/rs/1.0/resourcesync)

## installation

### prerequisites
* python3

```
git clone git@github.com:EHRI/resydes.git
cd resydes
mkdir logs
```
See for a more detailed guide the Wiki pages of this repo: https://github.com/EHRI/resydes/wiki/Installation-from-source

## running
to run a test, either test against your own ResourceSync Source, or use the [ResyncServer](https://github.com/EHRI/resyncserver).
```
git clone git@github.com:EHRI/resyncserver.git
cd resyncserver
python3 server.py
```
and in the resydes dir:
```
echo 'http://localhost:8000/srv/source1/loc1' > sources.txt
python3 des/desrunner.py -t discover sources.txt
```
you can add, update and delete files in the ResyncServer directory and see those changes reflected in the Destination.

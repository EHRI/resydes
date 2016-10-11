# Run Resydes as a Docker container

Resydes is a ResourceSync Framework Destination. It will repeatedly 
scan zero or more remote sites for ResourceSync Framework documents and
synchronize the found resources.

Resydes can be run as a [Docker](https://www.docker.com/) container. 
With the contents of this folder you can make a quick start. The file
`start.sh` has a bash script with a typical `docker run` command. The 
 folder `conf` contains configuration files and templates. Running
 Resydes with default settings will create the folders `logs` 
 and `destination`, which will be used for logging and for storing
 resources respectively. 

You can issue command line arguments when you run Resydes as a Docker
container. Resydes will run in default configuration if
you do not supply them. Run Resydes with deafault configuration and 
settings:

```
$ ./start.sh
```

### Getting help

```
$ ./start.sh -h
usage: startrunner.py [-h] [-s SOURCES] [-c] [-t] [-o]

Run a ResourceSync Destination.

optional arguments:
  -h, --help            show this help message and exit
  -s SOURCES, --sources SOURCES
                        the name of the file with source urls (default:
                        conf/sources.txt)
  -c , --config         the configuration filename (default: conf/config.txt)
  -t , --task           the task that should be run. ['discover', 'wellknown',
                        'capability'] (default: discover)
  -o, --once            explore source urls once and exit (default: False)
```

The help display originates from the `startrunner.py` that is the 
entrypoint of the docker container. Command line options given to
the start script are passed on to the python script in the container.

### Sources

The sources file is used to indicate which sites should
be visited during a run. The default name and location of this file
is `conf/sources.txt`. You can change name and location with 
the `-s` option. Resydes will read this file at the start of each
synchronization scan, so you can change the contents of this file
while Resydes is running.

How precise the urls you give in the sources file should be depends 
on the _task_ (see below) that Resydes is running. Tasks 'wellknown' and
'capability' demand urls that strictly point to ResourceSync
Framework documents of capability 'description' and 'capabilitylist'
respectively. Task 'discover' (the default) is less restrictive. 

In task mode 'discover' several extensions on the given url will be
tried and several strategies will be attempted to discover a
ResourceSync Framework tree at the remote site.
See __Tasks__ below for details on this.

### Configuration

The default location of the configuration file is `conf/config.txt`. 
You can change name and location of this file with the `-c` option.

The example configuration file at `conf/config.txt` has a short
descriptions of the options that can be set.

### Tasks

The task that should be run by Resydes. The task specifies in which
way Resydes will try to explore the remote site. Possible values
for the `-t` option are `capability`, `wellknown` and `discover`. The
default task is `discover`.

With task `wellknown` the urls in the sources file should point to
documents with capability `description` at the location
`/.well-known/resourcesync`. Resydes will synchronize the complete
tree of documents found through this decription document.

With task `capability` the urls in the sources file should directly 
point to documents with capability `capabilitylist`. 
Resydes will synchronize the complete
tree of documents found through these `capabilitylist` documents.

With task `discover` the urls in the sources file can point to
mixed locations. Site A might be discovered through the 
description file at `.well-known/resourcesync`, site B might be
discovered through links in the file `robots.txt`, while from site C
the resourclists mentioned in a specific capabilitylist are 
synchronized.

### Destination

Resydes will create a folder `destination` that will be the root for
all synchronized resources. The configuration parameter
`use_netloc` in the configuration file (see `conf/config.txt`)
takes a boolean and specifies whether the netloc part of source uri's
should be used as names for subdirectories.

The file `conf/desmap.txt` can be used to map sources to destination
folders.

### Drawbacks

Due to imperfections in the underlying
 [resync](https://github.com/resync/resync)
library there are some drawbacks and restrictions.

- A `resourcelist` document should be located in a folder that
is _upstream_ as seen from the resources it locates and both 
`resourcelist` and resources should be in the same branch of
the folder tree.
- This also implies restrictions on sets from the same site. 
Synchronizations of overlapping resource trees
originating from different sets or capabilitylists will
mutually erase one another.





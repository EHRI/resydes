# Run Resydes as a Docker container

Resydes is a ResourceSync Framework Destination. It will repeatedly 
scan zero or more remote sites for ResourceSync Framework documents and
synchronize the found resources.

Resydes can be run as a [Docker](https://www.docker.com/) container. 
With the contents of this folder you can make a quick start. The file
`start.sh` has a bash script with a typical `docker run` command. The 
 folder `conf` has typical configuration files or templates. Running
 Resydes with default settings will create the folders `logs` 
 and `destination`, which will be used for logging and for storing
 resources respectively. 

You can issue command line arguments when you run Resydes as a Docker
container. However, Resydes will run in default configuration if
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

### Setting sources

You can use the sources file to indicate which sites should
be visited during a run. The default name and location of this file
is `conf/sources.txt`. You can change name and location with 
the `-s` option. Resydes will read this file at the start of each
synchronization scan, so you can change the contents of this file
while Resydes is running.

How precise the urls you give in the sources file should be depends 
on the task (see below) that Resydes is running. Tasks 'wellknown' and
'capability' demand urls that strictly point to ResourceSync
Framework documents of capability 'description' and 'capabilitylist'
respectively. Task 'discover' (the default) is less restrictive. 

In task mode 'discover' several extensions on the given url will be
tried and several strategies will be attempted to discover a
ResourceSync Framework tree at the remote site.
See __Setting the task__ below for details on this.




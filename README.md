# Check Sharepoint Sync

Small tool that checks if the SharePoint Sync is working or not on a device (server).


## How does it work ?

You must install this script on 2 servers.  They will monitor each other.  One server will write a file in a given directory.  The other server, who should be syncing via SharePoint, will receive this file in the locally synced directory.  The second server will check the creation date of the files in that synced directory.  If the syncing fails, the creation date will become too old and a notification is sent.  The second server will also write his file to this synced directory and the first server will check this.  You can add as many servers as you want, they will all monitor the rest.


## Conda environment

At this moment, you must create a conda environment named check_sharepoint_sync and add the following packages as shown in the code below

````
conda create -y --name check_sharepoint_sync
conda activate check_sharepoint_sync
conda install -y -c conda-forge python=3.10 croniter pyyaml 
````

## Installation

Check out this git repository's main branch.  Then just run the "run.bat" script.  Best thing you can do, is installing a Windows service using "nssm" that starts the run.bat file.


## Configuration

See the config.yaml file.  The parameters should be straight forward.  If not, the truth is in the source.


## Questions

Contact Yves Vindevogel (sidviny - yves.vindevogel.external@arcelormittal.com) at ArcelorMittal Ghent (BE)
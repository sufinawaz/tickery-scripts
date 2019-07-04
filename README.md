## Installation

To set up start up script, please add the following code block before `exit 0` in `/etc/rc.local` file. You will need sudo access for this operation.
`python /home/pi/tickery-scripts/tickery.py || exit 1`

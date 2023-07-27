# Setup ADL-LRS locally:

1. Build an image from a Dockerfile:

`docker build . --tag=adl-lrs`

2. Create and run a new container from the image:

`docker run -it adl-lrs bash`

3. Now you are inside the container.


## Generate new migrations:

1. Create the `logs` folder in the root dir:

`mkdir logs`

3. Run `makemigrations` command: 

`python manage.py makemigrations`

4. Copying files from Docker container to host:

`sudo docker cp adl-lrs:/adl_lrs/lrs/migrations/0002_auto_20230727_0941.py .`
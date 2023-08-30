# Cycling sequence workflow example

## 1. Setup Container

First you need to set up a conteinerized environment capable of running AiiDAlab
(or at least aiica-core, for the purposes of this test).
There are many ways to do this, from using
[aiidalab-launch](https://github.com/aiidalab/aiidalab-launch)
to setting up your own Docker image.
A compromise of ease and versatility I found useful is to make a `docker-compose.yml` file with the already
existing AiiDAlab images:

```
version: "3.9"

services:

  aurora:
    image: "aiidalab/aiidalab-docker-stack:22.8.1"
    ports:
      - "8888:8888"
    volumes:
      - "data:/home/aiida/data"

volumes:
  data:
```

Then you can start it up by running (in the same folder) `docker-compose up`
(note that the terminal will then be blocked due to the running docker instance).
Then you can access the container via de jupyter lab interface (as the aiida user)
or running `docker exec -it ${CONTAINER_ID} /bin/bash` (as root).

Note that the data volume will be created automatically, and will serve the purpose
of data persistence.
Also, depending on how you will be working, you will need to remember to set up
your internal configuration to work with github (for example, some tools like vscode
plugins may allow you to open the files inside the container while using an external
github connection / credentials).
For me, this is just copying the ssh key inside the .ssh folder in the container and
then setting up the config file:

```
Host github.com
  User git
  HostName github.com
  IdentityFile ~/.ssh/github_key
  IdentitiesOnly yes
```

## 2. Install Tomato

It is better to install tomato in its own separate environment.
If you are using a container with conda (suche as the one used before), just run:

```
conda create --name tomato
conda activate tomato
```

You may also specify python version at the end of the first line (`python=3.9`).
Then you will have to install tomato, which can normally be done via PyPi package
(`pip install tomato`), see the
[docs](https://dgbowl.github.io/tomato/master/installation.html)
for more information.
However, if the PyPi package is broken, you may need to install it manually by
cloning the [git repository](https://github.com/dgbowl/tomato) and running

```
pip install -e .
```

You can start the tomato server by running `tomato -vv` (this will block the window).
You can check the available pipelines using:

```
$ ketchup status

pipeline             ready jobid  (PID)     sampleid
===================================================================
dummy-10             no    None             None
dummy-5              no    None             None
```

You can set up a sample with the following commands:

```
$ ketchup load commercial-10 dummy-10
$ ketchup ready dummy-10
$ ketchup status

pipeline             ready jobid  (PID)     sampleid
===================================================================
dummy-10             yes   None             commercial-10
dummy-5              no    None             None
```

## 3. Install AiiDA

Although AiiDA can normally be pip installed by itself or as a dependency of the
aurora-plugin and the aurora-app, the code is currently relying on a custom
adaptation of the code that is not included in the core release.
Although this should only affect the connection to windows clusters, it may be
more convenient to just set up that version anyways:

```
git clone https://github.com/lorisercole/aiida-core.git
cd aiida-core
git checkout windows
pip install -e .
```

NOTE: in some computers python still uses the `aiida-core` installed in the root
directory, so you may need to log in as root and install the package system-wide.

## 4. Install Aurora

The aurora plugin can also be installed via PyPi package
(and if you are installing the
[aiidalab-auror app](https://github.com/epfl-theos/aiidalab-aurora),
the plugin will be installed as a dependency).
However, if you are going to develop the package, you will probably prefer to clone
it from the [github repo](https://github.com/epfl-theos/aiida-aurora), or your own
fork.
In this case you may also want to install with `pip install -e .[pre-commit]` and
then do `pre-commit install` too.

Note that there is at least one line in the code that you may need to adapt in
order to run: the location of the ketchup executable.

```
diff --git a/aiida_aurora/scheduler.py b/aiida_aurora/scheduler.py
index dd42421..476a393 100644
--- a/aiida_aurora/scheduler.py
+++ b/aiida_aurora/scheduler.py
@@ -102,7 +102,7 @@ class TomatoScheduler(Scheduler):
-    KETCHUP = "ketchup"
+    KETCHUP = "/home/aiida/.conda/envs/tomato/bin/ketchup"
```

Once the package is installed, you can run:

```
reentry scan
verdi daemon restart --reset
```

And afterwards you should be able to check the new plugins by running:

```
verdi plugin list aiida.schedulers
verdi plugin list aiida.calculations
```

## 5. Database Setup

Finally, you need to set up the base computer and code to run.
The settings for these devices can be found in the `aiida-aurora/examples/config_tests`
folder, and can be installed by runnig:

```
verdi computer setup --config computer_localhost_tomato.yml

verdi computer configure local --config computer_localhost_tomato_config.yml localhost-tomato

verdi code setup --config code_ketchup-0.2rc2.yml
```

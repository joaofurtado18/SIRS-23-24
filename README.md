# T21 GrooveGalaxy Project Read Me

## Team

| Number | Name                  | User                               | E-mail                                            |
| ------ | --------------------- | ---------------------------------- | ------------------------------------------------- |
| 93634  | Diogo Faria Gonçalves | <https://github.com/DiFarGon>      | <mailto:diogo.faria.goncalves@tecnico.ulisboa.pt> |
| 99078  | Guilherme Carabalone  | <https://github.com/Carabalone>    | <mailto:guilherme.carabalone@tecnico.ulisboa.pt>  |
| 99095  | João Furtado          | <https://github.com/joaofurtado18> | <mailto:joao.melo.furtado@tecnico.ulisboa.pt>     |


## Contents

This repository contains documentation and source code for the _Network and Computer Security (SIRS)_ project.

The [REPORT](REPORT.md) document provides a detailed overview of the key technical decisions and various components of the implemented project.
It offers insights into the rationale behind these choices, the project's architecture, and the impact of these decisions on the overall functionality and performance of the system.

This document presents installation and demonstration instructions.

_(adapt all of the following to your project, changing to the specific Linux distributions, programming languages, libraries, etc)_

## Installation

To see the project in action, it is necessary to setup a virtual environment, with 1 network and 2 machines.

The following diagram shows the networks and machines:

```
+-------------------------+
|       VM: DB            |
|                         |
| eth0: 192.168.0.100      |
|                         |
+-----------|-------------+
            |
            |
+-----------|-------------+
|     Switch: sw-1        |
+-----------|-------------+
            |
+-------------------------+
|       VM: Server        |
|                         |
| eth0: 192.168.0.10      |
|                         |
+-----------|-------------+
            |
            |
+-----------|-------------+
|     Switch: sw-2        |
+-----------|-------------+
            |
            |
+-------------------------+
|       VM: Client 1      |
|                         |
| eth0: 192.168.0.50      |
|                         |
+-------------------------+
            |
            |
+-------------------------+
|       VM: Client 2      |
|                         |
| eth0: 192.168.0.51      |
|                         |
+-------------------------+
            |
            |
+-------------------------+
|       VM: Client 3      |
|                         |
| eth0: 192.168.0.52      |
|                         |
+-------------------------+
```

### Prerequisites

All the virtual machines are based on: Linux 64-bit, Kali 2023.3

[Download](https://www.kali.org/get-kali/#kali-installer-images) and [install](https://www.kali.org/docs/virtualization/install-virtualbox-guest-vm/) a virtual machine of Kali Linux 2023.3.  
Clone the base machine to create the other machines.

Create a base machine and for every following machine, make a linked clone, and select the option to generate new MAC addresses for all network ports.

### Machine configurations

For each machine, there is an initialization script with the machine name, with prefix `init-` and suffix `.sh`, that installs all the necessary packages and makes all required configurations in the a clean machine.

Inside each machine, use Git to obtain a copy of all the scripts and code.

```sh
$ git clone https://github.com/tecnico-sec/t21-joao-diogo-guilherme.git
```

Next we have custom instructions for each machine.

#### Server

This machine runs a flask HTTPS server that uses self signed certificates to ensure encryption.

You should first expose this virtual machine to switch sw-1 on adaptor 1, sw-2 on adaptor 2, and temporarily, NAT on adaptor 3 so you can clone the repository.
Also go to settings, network, and for every local network adaptor, select promiscuous mode: allow VMs
Go to the cloned directory and do:

```sh
$ sudo chmod +x init-server.sh
```

```sh
$ sudo ./init-server.sh
```

This should configure everything and start the server running in HTTPS

Also go to app/database.md and at the end of the document there is a tutorial explaining on how to set up the firewall
_(explain how to fix some known problem)_
We have a throubleshooting section below.

#### Database

You should expose this Virtual Machine to switch sw-1 on adaptor 1, and temporarily, NAT on adaptor 2 so you can clone the repository.
Also go to settings, network, and for every local network adaptor, select promiscuous mode: allow VMs

Setup up postgres and firewalls as explained in: app/database.md

Then run:

```sh
$ sudo chmod +x init-DB.sh
```

```sh
$ sudo ./init-DB.sh
```

This will set up your IP address and will fill the database with filler information.

#### Client:

You should expose this Virtual Machine to switch sw-2 on adaptor 1, and temporarily, NAT on adaptor 2 so you can clone the repository.
Also go to settings, network, and for every local network adaptor, select promiscuous mode: allow VMs

NOTE: Our client script specifially configures for ip 192.168.1.50, if you are running more than one client VM (you can run two clients in the same VM as long as they are in separate directories, i.e cloning the repository in two different directories), you have to change the ip for your desired ip address. For example you can use 192.168.1.x, as long as x is not one of the numbers previously used (100, 200, 50, 10)

If you need to edit the ip:

```sh
$ vim init-client.sh
```

and change to the desired IP address in the ifconfig eth0... line.

```sh
$ sudo chmod +x init-client.sh
```

```sh
$ sudo ./init-client.sh
```

This should install all dependencies and set up networks.

Then go to app/cli:

```sh
$ cd app/cli
```

And start the client:

```sh
$ python client.py
```

#### Troubleshooting

- Cant connect to the internet / Cant Install python dependencies

After a windows update, my VMs stopped connecting to the internet entirely, even the ones that were connecting previously. Specifically for the server VM, I found out that reconfiguring the network to have just a NAT on adaptor 2 made the internet work.
Thankfully we don't need internet to run our project, since it runs on an internal network, but we do need it to clone the repository and install dependencies. This issue happened very late in the day of delivery, so I don't have a permanent fix but I have a workaround. For all virtual machines where this problem is happening, setup the NAT in adapter 1 or 2. Don't bother with the internal network, then start the VM, and manually install the dependencies in the root directory of the project using:

```bash
$ sudo pip install -r requirements.txt
```

If you are doing firewall in this VM (e.g server or database), also install UFW

```bash
$ sudo apt-get install ufw
```

Then shut the VM off, and do the configuration as normal (in the server, for example, with sw-1 on adapter 1, sw-2 on adapter 2 and NAT on adapter 3) and run the init command as normal.

## Demonstration

Now that all the networks and machines are up and running, ...

With the server running, in each client machine go to the /cli directory

```sh
$ cd app/cli
```

Now let's run the client CLI and register 3 clients, one in each machine
Notice that the client app should be executed with an argument corresponding to its family key
file to simulate that the client and server already know each other

In client 1

```sh
$ python client.py fk1.pem
```

In client 2

```sh
$ python client.py fk2.pem
```

In client 3

```sh
$ python client.py fk3.pem
```

In each client you can now register using `reg`
The clients should be registered in order

After each client is registered you can now explore the app
If you quit and restart the app you no longer need to provide a command line argument

```sh
$ python client.py
```

Now that every client is registered, login as client 1 using `log`

After you login, there's multiple actions you can take:

- use `cat` to see the catalog of media
- use `cre` to create a new media item
- use `upd` to update a media item
- use `del` to delete a media item

Let's buy something! After looking at the catalog pick a media item you want to buy.
Now you can buy it by using `buy` followed by that _media item id_

Use `lib` to see your newly bought media item!
If you want to give it a listen use `get` followed by the _media id_

Enough of client 1, let's move on to client 2

Login as client 2 using `log`

- use `cat` and check that the media item bought by client 1 isn't for sale anymore
- if you try to `buy` the media owned by client 1 you will be presented an error message
- use `usr` to list the registered users
- use `fam` to list the registered families

Let's use `jfam` followed by _1_ to join family with _id 1_
Great! Now client 2 can access media items owned by client 1
Check it out by using `get` followed by the _id_ of the media you bought with client 1

Finally, let's login as client 3

use `fam` and confirm that client 1 and client 2 are part of the same family

Now use `get` followed by the _id_ of the media item bought by client 1
Confirm that it fails. That's because client 3 doesn't own that media item and isn't part of the family of the owner

_(give a tour of the best features of the application; add screenshots when relevant)_

```sh
$ demo command
```

_(replace with actual commands)_

_(IMPORTANT: show evidence of the security mechanisms in action; show message payloads, print relevant messages, perform simulated attacks to show the defenses in action, etc.)_

This concludes the demonstration.

## Additional Information

### Links to Used Tools and Libraries

- [Python 3.8](https://docs.python.org/pt-br/3.8/index.html)
- [Flask](https://flask.palletsprojects.com/en/3.0.x/)
- [Postgres 16](https://www.postgresql.org/docs/)
- ...

### Versioning

We use [SemVer](http://semver.org/) for versioning.

### License

This project is licensed under the MIT License - see the [LICENSE.txt](LICENSE.txt) for details.

_(switch to another license, or no license, as you see fit)_

---

END OF README

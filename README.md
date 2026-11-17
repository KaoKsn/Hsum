# Podman, APIs and Databases

## Setup

1.  Enable port 80 for the reverse proxy.

```
sudo -c 'echo "net.ipv4.ip_unprivileged_port_start = 80 >> /etc/sysctl.d/podman.conf'
```

The above allows podman containers to use privileged 80 port. In case you don't want to do, this change the port number in the compose file to a port >= 1024.

2. Run the setup script to create the required network and volume.

If you intend to use different network bridges or volumes, change them in the compose file and don't run the script

3. Install `podman` and `podman-compose` using your package manager

An example is given below.

```sh
sudo pacman -S podman podman-compose --noconfirm
```

## Running

> Use `make help` to check for the options and read the makefile to understand what they do.

Below is the code to build the image with release tag. Change the value of tag and don't forget to pass it to the compose file if you do so.

```sh
make TAG=release
make up
```

## Debug builds

If you wish to use debug builds when building the projects do so like this:

```sh
make BUILD_TYPE=debug
make up TAG=debug
```

To remove the debug image perform `make clean TAG=debug`

## Read more

Read more about [`podman`](https://podman.io), [`docker`](https://docs.docker.com) and `containers` through the formatted links given.

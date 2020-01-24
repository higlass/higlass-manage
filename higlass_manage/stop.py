import sys
import click
import docker

from .common import CONTAINER_PREFIX, NETWORK_PREFIX, REDIS_PREFIX


@click.command()
@click.argument("names", nargs=-1)
@click.option(
    "--remove-container/--dont-remove-container",
    default=True,
    show_default=True,
    help="Remove stopped higlass container",
)
@click.option(
    "--stop-redis/--dont-stop-redis",
    default=True,
    show_default=True,
    help="Stop and remove redis container"
    " associated with a given higlass"
    " instance.",
)
@click.option(
    "--remove-network-bridge/--dont-remove-network-bridge",
    default=True,
    show_default=True,
    help="Remove network bridge associated with a given higlass instance.",
)
def stop(
    names, remove_container, stop_redis, remove_network_bridge,
):
    _stop(
        names, remove_container, stop_redis, remove_network_bridge,
    )


def _stop(
    names, remove_container=True, stop_redis=True, remove_network_bridge=True,
):
    """
    Stop a running higlass instance along with the
    associated redis container and network bridges.

    The script attemps to stop and remove all of the
    containers/networks associated with a given higlass
    name.
    """
    client = docker.from_env()

    if len(names) == 0:
        names = ("default",)

    for name in names:
        # higlass container
        hm_name = "{}-{}".format(CONTAINER_PREFIX, name)
        try:
            client.containers.get(hm_name).stop()
            if remove_container:
                client.containers.get(hm_name).remove()
        except docker.errors.NotFound as ex:
            sys.stderr.write("Instance not running: {}\n".format(name))

        # redis container
        if stop_redis:
            redis_name = "{}-{}".format(REDIS_PREFIX, name)
            try:
                client.containers.get(redis_name).stop()
                client.containers.get(redis_name).remove()
            except docker.errors.NotFound:
                sys.stderr.write(
                    "No Redis instances found at {}; skipping...\n".format(redis_name)
                )

        # bridge network
        if remove_network_bridge:
            network_name = "{}-{}".format(NETWORK_PREFIX, name)
            try:
                network_list = client.networks.list(names=[network_name])
                if network_list:
                    network = client.networks.get(network_name)
                    network.remove()
            except docker.errors.NotFound:
                sys.stderr.write(
                    "No bridge network found at {}; skipping...\n".format(network_name)
                )

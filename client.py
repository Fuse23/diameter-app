import logging
import time
import threading
from argparse import ArgumentParser, Namespace
from diameter.message import Message

from diameter.message.constants import *
from diameter.message.commands.diameter_eap import DiameterEapRequest, DiameterEapAnswer
from diameter.node import Node
from diameter.node.peer import Peer
from diameter.node.application import Application, SimpleThreadingApplication


SERVER_NAME = "serve.test.realm"
REALM = "test.realm"


logging.basicConfig(
    format="%(asctime)s %(name)-22s %(levelname)-7s %(message)s",
    level=logging.CRITICAL,
)

# logging.getLogger("diameter.peer.msg").setLevel(logging.DEBUG)


def parse() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument(
        "server_ip",
        nargs='?',
        const=1,
        type=str,
        help="IP of diameter server",
    )
    parser.add_argument(
        "port",
        nargs='?',
        const=1,
        type=int,
        help="Port which server listen",
    )
    parser.add_argument(
        "count_of_clients",
        nargs='?',
        const=1,
        type=int,
        default=5,
        help="Count of client for create multiple requests",
    )

    return parser.parse_args()


def get_DER(app: Application) -> DiameterEapRequest:
    message = DiameterEapRequest()
    message.session_id = app.node.session_generator.next_id()
    message.origin_host = bytes(app.node.origin_host, "utf-8")
    message.origin_realm = bytes(app.node.realm_name, "utf-8")
    message.destination_realm = bytes(REALM, "utf-8")
    message.auth_request_type = 0
    message.destination_host = bytes(SERVER_NAME, "utf-8")

    return message


def get_node(number: int) -> Node:
    return Node(
        f"client{number}.test.realm",
        REALM
    )


def get_peer(node: Node, port: int, server_ip: str) -> Peer:
    return node.add_peer(
        f"aaa://{SERVER_NAME}:{port}",
        REALM,
        ip_addresses=[server_ip],
        is_persistent=True,
    )


def create_and_run_node(number: int, port: int, server_ip: str) -> None:
    node = get_node(number)
    peer = get_peer(node, port, server_ip)

    app = SimpleThreadingApplication(
        APP_EAP_APPLICATION,
        is_auth_application=True
    )

    node.add_application(app, [peer])

    node.start()

    app.wait_for_ready()
    answer = app.send_request(get_DER(app))

    if isinstance(answer, DiameterEapAnswer):
        print(threading.get_ident(), answer)

    node.stop()


def main() -> None:
    args = parse()

    threads = []
    for i in range(args.count_of_clients):
        thread = threading.Thread(target=create_and_run_node, kwargs={
            "number": i,
            "port": args.port,
            "server_ip": args.server_ip,
        })
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()


if __name__ == "__main__":
    main()

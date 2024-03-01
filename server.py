import logging
import time
import threading
from argparse import ArgumentParser, Namespace

from diameter.message.constants import *
from diameter.message import Message
from diameter.node import Node
from diameter.node.peer import Peer
from diameter.node.application import (
    SimpleThreadingApplication,
    Application,
    ThreadingApplication,
    _AnyAnswerType,
)


logging.basicConfig(
    format="%(asctime)s %(name)-22s %(levelname)-7s %(message)s",
    level=logging.CRITICAL,
)

# logging.getLogger("diameter.peer.msg").setLevel(logging.DEBUG)


class MyApp(ThreadingApplication):
    def handle_request(self, message: Message) -> Message | None:
        print(threading.get_ident(), message)
        answer = self.generate_answer(
            message,
            result_code=E_RESULT_CODE_DIAMETER_SUCCESS
        )

        return answer


def parse() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument(
        "server_ip",
        nargs='?',
        const=1,
        type=str,
        default="127.0.0.1",
    )
    parser.add_argument(
        "port",
        nargs='?',
        const=1,
        type=int,
        default=3868,
    )

    return parser.parse_args()


def get_node(ip: str, port: int) -> Node:
    return Node(
        origin_host="server.test.realm",
        realm_name="test.realm",
        ip_addresses=[ip],
        tcp_port=port,
    )


def add_peers(node: Node) -> list[Peer]:
    name_peers = get_peers()
    peers = []

    for peer in name_peers:
        peers.append(node.add_peer(peer_uri=peer))

    return peers


def get_peers() -> list[str]:
    peers = []

    for i in range(100):
        peers.append(f"aaa://client{i}.test.realm")

    return peers


def handle_request(app: Application, message: Message) -> _AnyAnswerType:
    print(f"{threading.get_ident()} Got: {message}")
    # logging.info()
    answer = app.generate_answer(
        message,
        result_code=E_RESULT_CODE_DIAMETER_SUCCESS
    )
    return answer


def get_app() -> Application:
    # return SimpleThreadingApplication(
    #     APP_EAP_APPLICATION,
    #     is_auth_application=True,
    #     max_threads=5,
    #     request_handler=handle_request,
    # )
    return MyApp(
        APP_EAP_APPLICATION,
        is_auth_application=True,
        max_threads=50,
    )


def main() -> None:
    args = parse()

    node = get_node(args.server_ip, args.port)
    peers = add_peers(node)
    app = get_app()
    node.add_application(app, peers)

    node.start()

    try:
        while True:
            time.sleep(1)

    except (KeyboardInterrupt, SystemExit) as e:
        node.stop()


if __name__ == "__main__":
    main()

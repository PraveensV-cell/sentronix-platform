import socket


def get_hostname() -> str:
    """
    Return the system hostname.
    """

    return socket.gethostname()


def get_local_ip() -> str:
    """
    Return the local IP address.
    """

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"


def check_network() -> bool:
    """
    Check internet connectivity.
    """

    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False

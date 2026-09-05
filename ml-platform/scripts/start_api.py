import subprocess
import sys


def start_server():

    print("Starting Sentronix AI API...")

    command = [
        sys.executable,
        "-m",
        "uvicorn",
        "api.inference_api:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
    ]

    subprocess.run(command)


def main():

    start_server()


if __name__ == "__main__":
    main()

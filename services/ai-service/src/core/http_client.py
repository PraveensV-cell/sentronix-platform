import httpx


class HTTPClient:
    """
    Shared HTTP client for all microservice communication.
    """

    def __init__(self):
        self.client = httpx.Client(
            timeout=30.0,
        )

    def get(self, url: str):
        response = self.client.get(url)
        response.raise_for_status()
        return response.json()

    def post(
        self,
        url: str,
        json=None,
    ):
        response = self.client.post(
            url,
            json=json,
        )
        response.raise_for_status()
        return response.json()

    def put(
        self,
        url: str,
        json=None,
    ):
        response = self.client.put(
            url,
            json=json,
        )
        response.raise_for_status()
        return response.json()

    def delete(
        self,
        url: str,
    ):
        response = self.client.delete(url)
        response.raise_for_status()
        return response.json()

    def close(self):
        self.client.close()


http_client = HTTPClient()

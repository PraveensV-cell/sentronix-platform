from typing import Any

import httpx


class ServiceClient:
    def __init__(
        self,
        base_url: str,
        timeout: int = 30,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def get(
        self,
        endpoint: str,
        params: dict | None = None,
    ) -> Any:

        async with httpx.AsyncClient(
            timeout=self.timeout,
        ) as client:
            response = await client.get(
                f"{self.base_url}{endpoint}",
                params=params,
            )

            response.raise_for_status()

            return response.json()

    async def post(
        self,
        endpoint: str,
        data: dict | None = None,
        json: dict | None = None,
        files=None,
    ) -> Any:

        async with httpx.AsyncClient(
            timeout=self.timeout,
        ) as client:
            response = await client.post(
                f"{self.base_url}{endpoint}",
                data=data,
                json=json,
                files=files,
            )

            response.raise_for_status()

            return response.json()

    async def put(
        self,
        endpoint: str,
        json: dict,
    ) -> Any:

        async with httpx.AsyncClient(
            timeout=self.timeout,
        ) as client:
            response = await client.put(
                f"{self.base_url}{endpoint}",
                json=json,
            )

            response.raise_for_status()

            return response.json()

    async def delete(
        self,
        endpoint: str,
    ) -> Any:

        async with httpx.AsyncClient(
            timeout=self.timeout,
        ) as client:
            response = await client.delete(
                f"{self.base_url}{endpoint}",
            )

            response.raise_for_status()

            return response.json()

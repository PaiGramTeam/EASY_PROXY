from typing import Dict

from fastapi import FastAPI
from httpx import (
    AsyncClient,
    RemoteProtocolError,
    UnsupportedProtocol,
    Response as HttpxResponse,
    ConnectError,
)
from starlette.requests import Request
from starlette.responses import Response

app = FastAPI()
WHITE_LIST = ["mihoyo.com", "miyoushe.com"]


def rewrite_headers(old_headers: Dict[str, str]) -> Dict[str, str]:
    remove_keys = ["host"]
    headers = {}
    for k, v in old_headers.items():
        if k.lower() not in remove_keys:
            headers[k] = v
    return headers


async def get_proxy(req: Request) -> Response:
    path = req.path_params.get("path")
    if not path:
        return Response(status_code=400, content="path is required")
    for domain in WHITE_LIST:
        if domain in path:
            break
    else:
        return Response(status_code=400, content="domain is not allowed")
    query = str(req.query_params)
    headers = rewrite_headers(dict(req.headers))
    method = req.method
    try:
        body = await req.body()
    except Exception as e:
        return Response(status_code=400, content=f"get request body info error: {e}")
    q = "?" + query if query else ""
    target_url = path + q
    async with AsyncClient(timeout=120, follow_redirects=True) as client:
        try:
            async with client.stream(
                method, target_url, headers=headers, data=body
            ) as r:
                headers = dict(r.headers)
                r: HttpxResponse
                _content = b"".join([part async for part in r.aiter_raw(1024 * 10)])
                return Response(_content, headers=headers, status_code=r.status_code)
        except (RemoteProtocolError, UnsupportedProtocol, ConnectError):
            return Response(content="UnsupportedProtocol", status_code=400)


app.add_route(
    "/{path:path}",
    get_proxy,
    methods=["OPTIONS", "HEAD", "GET", "POST", "PUT", "PATCH", "DELETE"],
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5677)

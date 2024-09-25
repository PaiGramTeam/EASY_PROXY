from typing import Dict

from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import Response
from env import proxy, cookies, old_uid, uid
from main import req_client

app = FastAPI()


def rewrite_headers(method: str, old_headers: Dict[str, str]) -> Dict[str, str]:
    remove_keys = ["host", "cookie"]
    headers = {}
    for k, v in old_headers.items():
        if k.lower() not in remove_keys:
            headers[k] = v
    if method not in ["OPTIONS"]:
        headers["cookie"] = cookies
        headers["x-rpc-language"] = "zh-cn"
        headers["x-rpc-lang"] = "zh-cn"
    return headers


async def get_proxy(req: Request) -> Response:
    path = req.path_params.get("path")
    if not path:
        return Response(status_code=400, content="path is required")
    host = req.headers.get("host")
    query = str(req.query_params).replace(str(old_uid), str(uid))
    method = req.method
    headers = rewrite_headers(method, dict(req.headers))
    try:
        body = await req.body()
    except Exception as e:
        return Response(status_code=400, content=f"get request body info error: {e}")
    q = "?" + query if query else ""
    target_url = f"https://{host}/" + path + q
    return await req_client(method, target_url, headers, body, proxy)


app.add_route(
    "/{path:path}",
    get_proxy,
    methods=["OPTIONS", "HEAD", "GET", "POST", "PUT", "PATCH", "DELETE"],
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5677)

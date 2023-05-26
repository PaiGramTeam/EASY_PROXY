from fastapi import FastAPI
from httpx import AsyncClient
from starlette.requests import Request
from starlette.responses import Response

app = FastAPI()
client = AsyncClient(
    timeout=60.0,
)


@app.get('/upload/{file_path:path}')
async def proxy_cve_search_api(req: Request, file_path: str) -> Response:
    headers = {}
    for i in req.headers.items():
        headers[i[0]] = i[1]
    headers["host"] = "upload-bbs.miyoushe.com"
    resp = await client.get(
        f'https://upload-bbs.miyoushe.com/upload/{file_path}',
        params=req.query_params,
        headers=headers,
        follow_redirects=True,
    )
    content = resp.content
    return Response(content=content, status_code=resp.status_code, headers=dict(resp.headers))


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5677)

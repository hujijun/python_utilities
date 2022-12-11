from service import sanic


@sanic.router(b"/")
async def test(request):
    return b'{"hello": "world"}'


if __name__ == "__main__":
    sanic.run(host="0.0.0.0", port=8000)

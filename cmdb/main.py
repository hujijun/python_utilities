from service import sanic
app = sanic.Sanic()


@app.router(b'/create')
async def create(request):
    return b'ok'


@app.router(b'/edit')
async def edit(request):
    return b'aaa'


@app.router(b'/delete')
async def delete(request):
    return b'aaa'


if __name__ == "__main__":
    app.run()

import logging
import api, utils


if __name__ == '__main__':
    utils.log.setLevel(logging.DEBUG)
    router = {
        b'/login': api.Login,
        b'/register': api.Register
    }
    utils.HttpProtocol.run(router)


import aiomysql


class aa(object):

    def aa(self):
        await aiomysql.create_pool(
            host=srvconf.mysql_host,
            port=srvconf.mysql_port,
            user=srvconf.mysql_user,
            password=srvconf.mysql_password,
            db=srvconf.database, loop=loop, charset='utf8', autocommit=True)
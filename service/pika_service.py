import logging
import time
import pika


class PiKaService(object):

    def __init__(self, url: str):
        self.url = pika.URLParameters(url)
        self._connection = self._channel = None

    @property
    def connection(self):
        """获取连接"""
        if not(self._connection and self._connection.is_open):
            self._connection = pika.BlockingConnection(self.url)
        return self._connection

    @property
    def channel(self):
        """获取管道"""
        if not(self._channel and self._channel.is_open):
            self._channel = self.connection.channel()
        return self._channel

    def close(self):
        if self._connection:
            self._connection.close()
        self._connection = self._channel = None

    def declare(self, exchange: str, queue: str, routing_key: str = None, exchange_type: str = 'direct'):
        # 声明交换机
        self.channel.exchange_declare(
            exchange=exchange,
            exchange_type=exchange_type,
            durable=True   # 持久化,重启后内容还在
        )
        # 声明队列
        self.channel.queue_declare(queue=queue, durable=True)
        # 将队列绑定路由，消息发到交换机，通过routing_key转发给指定的队列
        self.channel.queue_bind(exchange=exchange, queue=queue, routing_key=routing_key or queue)

    def publish(self, exchange_name, body, routing_key=''):
        properties = pika.BasicProperties(delivery_mode=2)
        self.channel.basic_publish(
            exchange=exchange_name,
            routing_key=routing_key,
            body=body,
            properties=properties)

    def start_consume(self, exchange, queue: str, callback_func):
        """启动监听队列"""
        self.declare(exchange, queue)
        while True:
            try:
                self.channel.basic_consume(queue, callback_func)
                logging.info(f"start consume {queue}")
                self.channel.start_consuming()
            except Exception as error:
                # 解决网络波动等异常重试
                logging.exception(error)
            finally:
                self.close()
            time.sleep(5)

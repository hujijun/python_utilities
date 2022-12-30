import logging
from pipeline.redis_service import RedisService

loger = logging.getLogger(__name__)

redis_service = RedisService("aa")


@celery.task(bind=True, base=MyCeleryBaseTask, max_retries=6)
def task_actuator_factory(self, task_id: int, sync_timestamp: int = 0) -> None:
    """ 任务执行器工厂方法 所有流程任务入口 """
    try:
        # db.session.commit()
        db.session.close()
        from service.data_center import DataCenterInfo
        start_time = int(time.time())
        task_inst = ''
        while True:
            db.session.commit()
            try:
                task_inst = task_base_impl.check_task(task_id)
            except execute.ExecuteException:
                if DataCenterInfo.is_leader:
                    raise execute.ExecuteException(f"获取工单数据出错,TaskId:{task_id}",
                                                   failed_type=task_enum.StepStateEnum.ERROR.value)
                utils.logger.exception("获取工单数据出错, TaskId:%s" % task_id)
                time.sleep(3)
                continue
            if int(sync_timestamp) <= int(task_inst.sync_timestamp):
                break
            if int(time.time()) - start_time >= 180:
                start_time = int(time.time())
                send_info = {
                    "game_id": task_inst.game_id,
                    "game_name": resource_service.game_operation.get_name(task_inst.game_id),
                    "region_id": task_inst.region_id,
                    "region_name": resource_service.region_operation.get_name(task_inst.game_id, task_inst.region_id),
                    "level": 2,
                    "task_id": task_inst.id,
                    "type": task_inst.remark.get("ding_title_type"),
                    "single_url": f"{settings.HOME_BASEURL}/task/detail/{task_inst.id}?gameId={task_inst.game_id}&gameRegionId={task_inst.region_id}"
                }
                title = task_inst.remark.get("ding_title_type") + '执行异常'
                content = "等待DB数据同步超时, 请检查DB数据同步是否异常!"
                send_mq_notice(title, content, [], send_info)
            time.sleep(3)
        if task_inst.session_id != self.request.id:
            utils.logger.info(f"taskId: {task_id} 会话Id:{self.request.id} 不相同退出执行")
            return
        task_type[task_inst.type](task_inst).init_and_start()
    except Exception as e:
        utils.logger.exception(e)
        raise self.retry(countdown=15)
    finally:
        db.session.close()
        db.session.remove()




@celery.task(bind=True, base=AtomCeleryBaseTask, max_retries=6)
def atom_actuator_factory(self, task_id: int, subtask_id: str, step: int, lifecycle: int):
    """原子执行器工厂方法"""
    lock_key = f"lock:{task_id}_{subtask_id}_{step}"
    lifecycle_lock_key = f"lock:{task_id}_{subtask_id}_{step}_{lifecycle}_lifecycle"
    log_prefix = f"{task_id}:{subtask_id}:{step}:{lifecycle}"
    lock_uuid = None

    def get_task_inst():
        db.session.close()
        db.session.commit()
        task_inst = task_base_impl.check_task(task_id)
        if task_inst.status in (task_enum.OrderStateEnum.Executing.value, task_enum.OrderStateEnum.ExecuteFailed.value):
            return task_inst
        elif task_inst.status == task_enum.OrderStateEnum.Approved.value:
            # 待执行状态，解决数据库同步问题 3 > 6 > 3
            utils.logger.info(f"{log_prefix} 当前任务状态为待执行, 放行并尝试修正任务状态")
            return task_inst
        utils.logger.info(f"{log_prefix} 当前任务状态: {task_enum.OrderStateEnum(task_inst.status).name} 不匹配 [待执行/执行中/执行失败] 的状态, 任务丢弃")
    try:
        task_inst = get_task_inst()
        if not task_inst:
            return
        lock_uuid = redis_service.get_lock(lock_key, 60)
        storage_block = block.Block(task_inst)
        try:
            subtask_info = storage_block.get_subtask_info(subtask_id)
        except:
            """
            获取子任务数据出错时重新检查一遍工单状态，防止延时检查任务和agent激活成功的任务同时进来，
            agent激活成功的任务先获取锁并入库清除任务数据释放锁后，延时检查任务这时获取到锁然后获取任务数据出错的问题
            """
            if not get_task_inst():
                return
            raise execute.ExecuteException('获取子任务数据出错', failed_type=task_enum.StepStateEnum.ERROR.value)

        # 检查如果lifecycle锁存在，从Redis取最新的值重新赋值给lifecycle
        if storage_block.conn.get(lifecycle_lock_key):
            lifecycle = subtask_info.get('lifecycle')
            utils.logger.info(
                f"检查lifecycle锁存在:{lifecycle_lock_key}, 从Redis取最新的值重新赋值给lifecycle, lifecycle最新值:{lifecycle}")
        if lifecycle >= subtask_info.get('lifecycle') and step == subtask_info.get('current_step'):
            if not storage_block.conn.get(lifecycle_lock_key):
                # lifecycle加1前进行加锁操作，防止任务执行到一半超时检查任务还没发出去,合代码worker重启导致的任务丢失
                redis_service.get_lock(lifecycle_lock_key, 24 * 60 * 60, lifecycle_lock_key)
            task_engine = task_type[task_inst.type](task_inst)
            atom_info = task_engine.block.get_atom_info(subtask_id, step)
            subtask_info['lifecycle'] += 1
            storage_block.update_subtask_info(subtask_id, subtask_info)
            utils.logger.info(f"{log_prefix} lifecycle+1")
            try:
                task_engine.AtomEnum[atom_info.get('func')].value(task_engine, subtask_id, step, subtask_info,
                                                                  atom_info).run()
                redis_service.unlock(lifecycle_lock_key, lifecycle_lock_key)
            except Exception as e:
                # utils.logger.exception(f"{log_prefix} 执行异常")
                subtask_info = storage_block.get_subtask_info(subtask_id)
                subtask_info['lifecycle'] -= 1
                storage_block.update_subtask_info(subtask_id, subtask_info)
                raise e
        else:
            utils.logger.info(
                f"{log_prefix} 当前step:{subtask_info.get('current_step')},lifecycle:{subtask_info.get('lifecycle')} 步骤号或lifecycle不匹配,任务丢弃")
    except Exception as e:
        utils.logger.exception(f"{log_prefix} 执行异常")
        raise self.retry(countdown=10)
    finally:
        if lock_uuid:
            redis_service.unlock(lock_key, lock_uuid)
        db.session.close()
        db.session.remove()
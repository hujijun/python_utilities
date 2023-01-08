import { PlusOutlined } from '@ant-design/icons';
import {Button, Card, List, message, Typography} from 'antd';
import { PageContainer } from '@ant-design/pro-layout';
import { addModel, updateMode, modeList } from '@/services/cmdb';
import styles from './style.less';
import { useRequest } from '@umijs/max';
import UpdateForm from "@/pages/cmdb/Repository/components/UpdateForm";
import AddModeForm from "@/pages/cmdb/Repository/components/AddModeForm";
import React, {useState} from "react";

const { Paragraph } = Typography;

const handleAdd = async (fields: API.ModeListItem) => {
  const hide = message.loading('Configuring');
  try {
    await addModel(fields);
    hide();
    message.success('Configuration is successful');
    return true;
  } catch (error) {
    hide();
    message.error('Configuration failed, please try again!');
    return false;
  }
};

const handleUpdate = async (fields: API.ModeListItem) => {
  const hide = message.loading('Configuring');
  try {
    await updateMode(fields);
    hide();
    message.success('Configuration is successful');
    return true;
  } catch (error) {
    hide();
    message.error('Configuration failed, please try again!');
    return false;
  }
};


const Repository = () => {
  const [modelType, setModelType] = useState<number>(1);
  const [currentRow, setCurrentRow] = useState<API.ModeListItem>();
  const { data, loading } = useRequest(() => {
    return modeList();
  });
  const content = (
    <div className={styles.pageHeaderContent}>
      <p>
        段落示意：蚂蚁金服务设计平台 ant.design，用最小的工作量，无缝接入蚂蚁金服生态，
        提供跨越设计与开发的体验解决方案。
      </p>
      <div className={styles.contentLink}>
        <a>
          <img alt="" src="https://gw.alipayobjects.com/zos/rmsportal/MjEImQtenlyueSmVEfUD.svg" />{' '}
          快速开始
        </a>
        <a>
          <img alt="" src="https://gw.alipayobjects.com/zos/rmsportal/NbuDUAuBlIApFuDvWiND.svg" />{' '}
          产品简介
        </a>
        <a>
          <img alt="" src="https://gw.alipayobjects.com/zos/rmsportal/ohOEPSYdDTNnyMbGuyLb.svg" />{' '}
          产品文档
        </a>
      </div>
    </div>
  );

  const extraContent = (
    <div className={styles.extraImg}>
      <img src="https://gw.alipayobjects.com/zos/rmsportal/RzwpdLnhmvDJToTdfDPe.png"/>
    </div>
  );
  return (
    <PageContainer
      content={content}
      extraContent={extraContent}>
      { modelType === 1 && (
        <div className={styles.cardList}>
          <List<Partial<API.ModeListItem>>
            rowKey="_id"
            loading={loading}
            grid={{gutter: 16, xs: 1, sm: 2, md: 3, lg: 3, xl: 4, xxl: 4}}
            dataSource={[{}, ...data || []]}
            renderItem={(item) => {
              if (item && item._id) {
                return (
                  <List.Item key={item._id}>
                    <Card
                      hoverable
                      className={styles.card}
                      actions={[
                        <a key="option1" onClick={() => {setCurrentRow(item);setModelType(3)}}>编辑</a>,
                        <a key="option2">关系</a>,
                        <a key="option3">删除</a>,
                      ]}>
                      <Card.Meta avatar={<img alt="" className={styles.cardAvatar} src={item.avatar} />} title={<a>{item.name}</a>}
                        description={<Paragraph className={styles.item} ellipsis={{ rows: 3 }}>{item.tableName}</Paragraph>}
                      />
                    </Card>
                  </List.Item>
                );
              }
              return (
                <List.Item>
                  <Button type="dashed" className={styles.newButton} onClick={() => {setModelType(2)}}>
                    <PlusOutlined /> 新增模型
                  </Button>
                </List.Item>
              );
            }}
          />
        </div>
      )}
      {modelType === 2 && (
        <AddModeForm
          onSubmit={async (value) => {
            const success = await handleAdd(value);
            if (success) {
              setModelType(1);
              // if (actionRef.current) {
              //   actionRef.current.reload();
              // }
            }}
        }
          />)}
      {/*{modelType === 3 && (*/}
      {/*  <UpdateForm*/}
      {/*    onSubmit={async (value) => {*/}
      {/*      const success = await handleUpdate(value);*/}
      {/*      if (success) {*/}
      {/*        setModelType(1);*/}
      {/*      }*/}
      {/*    }}*/}
      {/*    onCancel={() => {setModelType(1);}}*/}
      {/*    values={currentRow || {}}*/}
      {/*  />)}*/}
    </PageContainer>
  );
};

export default Repository;

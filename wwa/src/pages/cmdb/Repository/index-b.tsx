import {ActionType, ModalForm, PageContainer, ProFormText, ProFormTextArea} from '@ant-design/pro-components';
import { useIntl, useModel } from '@umijs/max';
import React, {useRef, useState} from 'react';
import {Button, message, Card, Col, Row } from "antd";
import {addModel} from "@/services/cmdb";
import {FormattedMessage} from "@@/exports";
import {PlusOutlined} from "@ant-design/icons";


const handleAdd = async (fields: API.RuleListItem) => {
  const hide = message.loading('正在添加');
  try {
    await addModel({ ...fields });
    hide();
    message.success('Added successfully');
    return true;
  } catch (error) {
    hide();
    message.error('Adding failed, please try again!');
    return false;
  }
};
const BusinessView: React.FC = () => {
  const intl = useIntl();
  const [createModalOpen, handleModalOpen] = useState<boolean>(false);
  const actionRef = useRef<ActionType>();
  const { initialState } = useModel('@@initialState');
  console.log(initialState?.currentUser?.authority)
  return (
    <PageContainer header={{extra: [<Button key="3" type="primary" onClick={() => {handleModalOpen(true)}}><PlusOutlined />新增</Button>]}}>
    {/*<PageContainer header={{title: "",breadcrumb: {}}}>*/}
      {'admin' in initialState?.currentUser?.authority && (
        <Button type="primary"  >
          <PlusOutlined /> <FormattedMessage id="pages.repository.newModl" />
        </Button>
      )}
       <Row gutter={16}>
      <Col span={4}>
        <Card bordered={false}>
          Card content
        </Card>
      </Col>
      <Col span={4}>
        <Card bordered={false}>
          Card content
        </Card>
      </Col>
      <Col span={4}>
        <Card bordered={false}>
          Card content
        </Card>
      </Col>
         <Col span={4}>
        <Card bordered={false}>
          Card content
        </Card>
      </Col>
         <Col span={4}>
        <Card bordered={false}>
          Card content
        </Card>
      </Col>
         <Col span={4}>
        <Card bordered={false}>
          Card content
        </Card>
      </Col>
    </Row>
      <p style={{ textAlign: 'center', marginTop: 24 }}>
        Want to add more pages? Please refer to{' '}
        <a href="https://pro.ant.design/docs/block-cn" target="_blank" rel="noopener noreferrer">use block</a>。
      </p>
      <ModalForm title={intl.formatMessage({id: 'pages.repository.createForm.newModl'})}
        width="400px"
        open={createModalOpen}
        onOpenChange={handleModalOpen}
        onFinish={async (value) => {
          const success = await handleAdd(value as API.RuleListItem);
          if (success) {
            handleModalOpen(false);
            if (actionRef.current) {
              actionRef.current.reload();
            }
          }
        }}
      >
        <ProFormText rules={[{required: true, message: (<FormattedMessage id="pages.repository.ruleName"/>)}]} width="md" name="name"/>
        <ProFormTextArea width="md" name="desc" />
      </ModalForm>
    </PageContainer>
  );
};

export default BusinessView;

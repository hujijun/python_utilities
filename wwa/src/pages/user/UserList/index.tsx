import { userList, updateUser } from '@/services/user';
import { PlusOutlined } from '@ant-design/icons';
import type { ActionType, ProColumns, ProDescriptionsItemProps } from '@ant-design/pro-components';
import {
  FooterToolbar,
  ModalForm,
  PageContainer,
  ProDescriptions,
  ProFormText,
  ProFormTextArea,
  ProTable,
} from '@ant-design/pro-components';
import { FormattedMessage, useIntl } from '@umijs/max';
import { Button, Drawer, Input, message } from 'antd';
import React, { useRef, useState } from 'react';
import type { FormValueType } from './components/UpdateForm';
import UpdateForm from './components/UpdateForm';


const handleAdd = async (fields: API.UserListItem) => {
  const hide = message.loading('正在添加');
  try {
    // await addModel({ ...fields });
    hide();
    message.success('Added successfully');
    return true;
  } catch (error) {
    hide();
    message.error('Adding failed, please try again!');
    return false;
  }
};

const handleUpdate = async (fields: FormValueType) => {
  const hide = message.loading('Configuring');
  try {
    await updateUser({_id: fields._id, isLogin: fields.isLogin});
    hide();
    message.success('Configuration is successful');
    return true;
  } catch (error) {
    hide();
    message.error('Configuration failed, please try again!');
    return false;
  }
};


const TableList: React.FC = () => {
  const [createModalOpen, handleModalOpen] = useState<boolean>(false);
  const [updateModalOpen, handleUpdateModalOpen] = useState<boolean>(false);
  const [showDetail, setShowDetail] = useState<boolean>(false);
  const actionRef = useRef<ActionType>();
  const [currentRow, setCurrentRow] = useState<API.UserListItem>();
  const [selectedRowsState, setSelectedRows] = useState<API.UserListItem[]>([]);
  const intl = useIntl();
  const columns: ProColumns<API.UserListItem>[] = [
    {title: "id", dataIndex: '_id', tip: 'xx', search: false,
      render: (dom, entity) => {
        return (<a onClick={() => {
          setCurrentRow(entity);
          setShowDetail(true)}}>{dom}
        </a>);
      },
    },
    {title: "用户", dataIndex: 'name', valueType: 'textarea'},
    {
      title: "限制登陆",
      dataIndex: 'isLogin',
      sorter: true,
      hideInSearch: true,
      renderText: (val: boolean) => `${val}`,
      // renderText: (val: boolean) => `${val}${' 万 '}`,
    },
    {title: "创建时间", dataIndex: 'createBy', sorter: true, valueType: 'textarea'},
    // {title: "上次登陆时间", dataIndex: 'createBy', valueType: 'textarea'},
    // {title: "更新时间", sorter: true, dataIndex: 'updatedAt', valueType: 'dateTime',
    //   renderFormItem: (item, { defaultRender, ...rest }, form) => {
    //     const status = form.getFieldValue('status');
    //     if (`${status}` === '0') {
    //       return false;
    //     }
    //     if (`${status}` === '3') {
    //       return (
    //         <Input {...rest} placeholder={intl.formatMessage({id: 'pages.searchTable.exception', defaultMessage: 'Please enter the reason for the exception!'})}/>
    //       );
    //     }
    //     return defaultRender(item);
    //   },
    // },
    {title: "操作", dataIndex: 'option', valueType: 'option',
      render: (_, record) => [
        <a key="config" onClick={() => {handleUpdateModalOpen(true);setCurrentRow(record)}}>
          配置
        </a>
      ],
    },
  ];

  return (
    <PageContainer header={{title: ""}}>
      <ProTable<API.UserListItem, API.PageParams>
        headerTitle={""}
        actionRef={actionRef}
        rowKey="_id"

        toolBarRender={() => [
          <Button type="primary" key="primary" onClick={() =>
            {handleModalOpen(true)}}><PlusOutlined /> 新建
          </Button>
        ]}
        request={userList}
        columns={columns}
        rowSelection={{onChange: (_, selectedRows) => {setSelectedRows(selectedRows)}}}
      />
      {selectedRowsState?.length > 0 && (
        <FooterToolbar
          extra={
            <div>
              <FormattedMessage id="pages.searchTable.chosen" defaultMessage="Chosen" />{' '}
              <a style={{ fontWeight: 600 }}>{selectedRowsState.length}</a>{' '}
              <FormattedMessage id="pages.searchTable.item" defaultMessage="项" />
              &nbsp;&nbsp;
              <span>
                <FormattedMessage id="pages.searchTable.totalServiceCalls" defaultMessage="Total number of service calls"/>{' '}
                {selectedRowsState.reduce((pre, item) => pre + item._id!, 0)}{' '}
                <FormattedMessage id="pages.searchTable.tenThousand" defaultMessage="万" />
              </span>
            </div>
          }
        >
          <Button onClick={async () => {
              // await handleRemove(selectedRowsState);
              setSelectedRows([]);
              actionRef.current?.reloadAndRest?.();
            }}
          >
            <FormattedMessage id="pages.searchTable.batchDeletion" defaultMessage="Batch deletion"/>
          </Button>
          <Button type="primary">
            <FormattedMessage id="pages.searchTable.batchApproval" defaultMessage="Batch approval"/>
          </Button>
        </FooterToolbar>
      )}
      <ModalForm
        title={intl.formatMessage({id: 'pages.searchTable.createForm.newRule', defaultMessage: 'New rule'})}
        width="400px"
        open={createModalOpen}
        onOpenChange={handleModalOpen}
        onFinish={async (value) => {
          const success = await handleAdd(value as API.UserListItem);
          if (success) {
            handleModalOpen(false);
            if (actionRef.current) {
              actionRef.current.reload();
            }
          }
        }}
      >
        <ProFormText
          rules={[{required: true, message: "Rule name is required"}]}
          width="md"
          name="name"
        />
        <ProFormTextArea width="md" name="desc" />
      </ModalForm>
      <UpdateForm
        onSubmit={async (value) => {
          const success = await handleUpdate(value);
          if (success) {
            handleUpdateModalOpen(false);
            setCurrentRow(undefined);
            if (actionRef.current) {
              actionRef.current.reload();
            }
          }
        }}
        onCancel={() => {
          handleUpdateModalOpen(false);
          if (!showDetail) {
            setCurrentRow(undefined);
          }
        }}
        updateModalOpen={updateModalOpen}
        values={currentRow || {}}
      />

      <Drawer
        width={600}
        open={showDetail}
        onClose={() => {setCurrentRow(undefined);setShowDetail(false)}}
        closable={false}
      >
        {currentRow?.username && (
          <ProDescriptions<API.UserListItem>
            column={2}
            title={currentRow?.username}
            request={async () => ({data: currentRow || {}})}
            params={{id: currentRow?.username}}
            columns={columns as ProDescriptionsItemProps<API.UserListItem>[]}
          />
        )}
      </Drawer>
    </PageContainer>
  );
};

export default TableList;

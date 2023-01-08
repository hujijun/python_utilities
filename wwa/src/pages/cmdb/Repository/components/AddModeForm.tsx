import { CloseCircleOutlined, SmileOutlined } from '@ant-design/icons';
import { ProForm, ProFormGroup, ProFormList, ProFormText, ProFormRadio, ProFormSelect } from '@ant-design/pro-components';
import React from 'react';


type FormProps = {
  onSubmit: (values: API.ModeListItem) => Promise<void>;
};

const AddModeForm: React.FC<FormProps> = (props) => {
  let formData = {
    "fields": [{value: '', label: ''}]
  }
  return  (
    <ProForm onFinish={props.onSubmit()}>
      <ProFormText name="name" label="资源名称" />
      <ProFormList name="labels" label="字段"
        initialValue={formData.fields}
        copyIconProps={{ Icon: SmileOutlined, tooltipText: '复制此行到末尾' }}
        deleteIconProps={{Icon: CloseCircleOutlined, tooltipText: '不需要这行了'}}>
        <ProFormGroup key="group">
          <ProFormText name="name" label="值" placeholder="字段名称" />
          <ProFormSelect name="select2" label="Select"
            request={async () => [{ label: '全部', value: 'all' }, { label: '未解决', value: 'open' },
              { label: '已解决', value: 'closed' },
              { label: '解决中', value: 'processing' },
            ]}
            placeholder="Please select a country"
            rules={[{ required: true, message: 'Please select your country!' }]}
          />
          <ProFormText name="name" label="值" placeholder="字段名称" />
          <ProFormRadio.Group name="radio-group" label="Radio.Group" options={[{label: '是否必填', value: 'a'}]}/>
        </ProFormGroup>
      </ProFormList>
    </ProForm>
  );
};

export default AddModeForm;

import { PageContainer } from '@ant-design/pro-components';
import { useIntl } from '@umijs/max';
import React from 'react';
import {Button} from "antd";

const BusinessView: React.FC = () => {
  const intl = useIntl();
  return (
    <PageContainer content={intl.formatMessage({id: 'pages.cmdb.businessView.title'})}>
      <Button type="primary">新增资源</Button>
      <p style={{ textAlign: 'center', marginTop: 24 }}>
        Want to add more pages? Please refer to{' '}
        <a href="https://pro.ant.design/docs/block-cn" target="_blank" rel="noopener noreferrer">use block</a>。
      </p>
    </PageContainer>
  );
};

export default BusinessView;

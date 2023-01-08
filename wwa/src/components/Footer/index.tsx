import { GithubOutlined } from '@ant-design/icons';
import { DefaultFooter } from '@ant-design/pro-components';
import { useIntl } from '@umijs/max';
import React from 'react';

const Footer: React.FC = () => {
  const intl = useIntl();
  const defaultMessage = intl.formatMessage({id: 'app.copyright.produced'});
  const currentYear = new Date().getFullYear();
  return (
    <DefaultFooter style={{background: 'none'}}
      copyright={`${currentYear} ${defaultMessage}`}
      links={[
        {
          key: 'AutoOps',
          title: 'AutoOps',
          href: 'https://www.abc.com',
          blankTarget: true,
        },
        {
          key: 'github',
          title: <GithubOutlined />,
          href: 'https://github.com/ant-design/ant-design-pro',
          blankTarget: true,
        }
      ]}
    />
  );
};

export default Footer;

import Footer from '@/components/Footer';
import { login } from '@/services/user';
import {LockOutlined, UserOutlined} from '@ant-design/icons';
import {LoginForm, ProFormCheckbox, ProFormText} from '@ant-design/pro-components';
import { useEmotionCss } from '@ant-design/use-emotion-css';
import { FormattedMessage, history, SelectLang, useIntl } from '@umijs/max';
import { Alert, message } from 'antd';
import React, { useState } from 'react';
import {useModel} from "@@/exports";
import { flushSync } from 'react-dom';

const Lang = () => {
  const langClassName = useEmotionCss(({ token }) => {
    return {
      width: 42,
      height: 42,
      lineHeight: '42px',
      position: 'fixed',
      right: 16,
      borderRadius: token.borderRadius,
      ':hover': {backgroundColor: token.colorBgTextHover},
    };
  });
  return (<div className={langClassName} data-lang>{SelectLang && <SelectLang />}</div>);
};


const Login: React.FC = () => {
  const [loginState, setLoginState] = useState<string>();
  const { setInitialState } = useModel('@@initialState');
  const containerClassName = useEmotionCss(() => {
    return {
      display: 'flex',
      flexDirection: 'column',
      height: '100vh',
      overflow: 'auto',
      backgroundImage: "url('https://mdn.alipayobjects.com/yuyan_qk0oxh/afts/img/V-_oS6r-i7wAAAAAAAAAAAAAFl94AQBr')",
      backgroundSize: '100% 100%'};
  });

  const intl = useIntl();
  const handleSubmit = async (values: API.LoginParams) => {
    try {
      // 登录
      const currentUser = await login(values);
      if (currentUser?.token) {
        message.success(intl.formatMessage({id: 'pages.login.success'}));
        flushSync(() => {setInitialState((s) => ({...s, currentUser }))});
        localStorage.setItem("currentUser", JSON.stringify(currentUser));
        const urlParams = new URL(window.location.href).searchParams;
        history.push(urlParams.get('redirect') || '/');
        return;
      }
      // 如果失败去设置用户错误信息
      setLoginState('error');
    } catch (error) {
      setLoginState('error');
      // message.error(intl.formatMessage({id: 'pages.user.failure', defaultMessage: '登录失败，请重试！'}));
    }
  };

  return (
    <div className={containerClassName}>
      <Lang />
      <div style={{flex: '1', padding: '32px 0'}}>
        <LoginForm
          contentStyle={{minWidth: 280, maxWidth: '75vw'}}
          logo={<img alt="logo" src="/favicon.ico" />}
          title="AutoOps"
          subTitle={intl.formatMessage({ id: 'pages.layouts.userLayout.title' })}
          initialValues={{autoLogin: true}}
          onFinish={async (values) => {await handleSubmit(values as API.LoginParams)}}
        >

          {
            loginState === 'error' && (
              <Alert style={{marginBottom: 24}} message={intl.formatMessage({id: 'pages.login.accountLogin.errorMessage'})} type="error" showIcon/>
            )}
          <ProFormText
            name="username"
            fieldProps={{size: 'large', prefix: <UserOutlined />}} placeholder={intl.formatMessage({id: 'pages.login.username.placeholder'})}
            rules={[{required: true, message: (<FormattedMessage id="pages.login.username.required" defaultMessage="请输入用户名!"/>)}]}
          />
          <ProFormText.Password
            name="password"
            fieldProps={{size: 'large', prefix: <LockOutlined />}} placeholder={intl.formatMessage({id: 'pages.login.password.placeholder'})}
            rules={[{required: true, message: (<FormattedMessage id="pages.login.password.required" defaultMessage="请输入密码！"/>)}]}
          />
          <div style={{marginBottom: 24}}>
            <ProFormCheckbox noStyle name="autoLogin">
              <FormattedMessage id="pages.login.rememberMe" defaultMessage="自动登录" />
            </ProFormCheckbox>
            {/*<a style={{float: 'right'}}>*/}
            {/*  <FormattedMessage id="pages.user.forgotPassword" defaultMessage="忘记密码" />*/}
            {/*</a>*/}
          </div>
        </LoginForm>
      </div>
      <Footer />
    </div>
  );
};

export default Login;

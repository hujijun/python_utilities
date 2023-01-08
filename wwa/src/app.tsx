import React from 'react';
import type { Settings as LayoutSettings } from '@ant-design/pro-components';
import type { RequestOptions } from '@@/plugin-request/request';
import type { RequestConfig, RunTimeLayoutConfig } from '@umijs/max';
import Footer from '@/components/Footer';
import RightContent from '@/components/RightContent';
import { history } from '@umijs/max';
import { message } from 'antd';
import { SettingDrawer } from '@ant-design/pro-components';
import defaultSettings from '../config/defaultSettings';

const loginPath = '/user/login';

/**
 * @see  https://umijs.org/zh-CN/plugins/plugin-initial-state
 * */
export async function getInitialState(): Promise<{settings?: Partial<LayoutSettings>; currentUser?: API.CurrentUser; loading?: boolean}> {
  // 如果不是登录页面，执行
  if (history.location.pathname !== loginPath) {
      const currentUser = localStorage.getItem("currentUser")
      if (currentUser) {
        return {settings: defaultSettings, currentUser: JSON.parse(currentUser)};
      }
  }
  return {settings: defaultSettings};
}

// ProLayout 支持的api https://procomponents.ant.design/components/layout
export const layout: RunTimeLayoutConfig = ({ initialState, setInitialState }) => {
  return {
    rightContentRender: () => <RightContent />,
    waterMarkProps: {content: initialState?.currentUser?.name},
    footerRender: () => <Footer />,
    onPageChange: () => {
      if (!initialState?.currentUser?.name && history.location.pathname !== loginPath) {
        history.push(loginPath)
      }},
    layoutBgImgList: [
      {
        src: 'https://mdn.alipayobjects.com/yuyan_qk0oxh/afts/img/D2LWSqNny4sAAAAAAAAAAAAAFl94AQBr',
        left: 85,
        bottom: 100,
        height: '303px',
      },
      {
        src: 'https://mdn.alipayobjects.com/yuyan_qk0oxh/afts/img/C2TWRpJpiC0AAAAAAAAAAAAAFl94AQBr',
        bottom: -68,
        right: -45,
        height: '303px',
      },
      {
        src: 'https://mdn.alipayobjects.com/yuyan_qk0oxh/afts/img/F6vSTbj8KpYAAAAAAAAAAAAAFl94AQBr',
        bottom: 0,
        left: 0,
        width: '331px',
      },
    ],
    links: [],
    // links: isDev ? [<Link key="openapi" to="/umi/plugin/openapi" target="_blank"><LinkOutlined /><span>OpenAPI 文档</span></Link>] : [],
    menuHeaderRender: undefined,
    // 自定义 403 页面
    // unAccessible: <NoFoundPage />,
    childrenRender: (children) => {
      // 增加一个 loading 的状态
      // if (initialState?.loading) return <PageLoading />;
      return (
        <>
          {children}
          <SettingDrawer
            disableUrlParams
            enableDarkTheme
            settings={initialState?.settings}
            onSettingChange={(settings) => {setInitialState((preInitialState) => ({...preInitialState, settings}))}}
          />
        </>
      );
    },
    ...initialState?.settings,
  };
};


/**
 * @name request 配置，可以配置错误处理
 * 它基于 axios 和 ahooks 的 useRequest 提供了一套统一的网络请求和错误处理方案。
 * @doc https://umijs.org/docs/max/request#配置
 */
export const request: RequestConfig = {
  // 错误处理： umi@3 的错误处理方案 https://umijs.org/docs/max/request#配置
  errorConfig: {
    // 错误接收及处理
    errorHandler: (error: any, opts: any) => {
      if (error.response.status === 401) {
        history.push(loginPath.concat('?redirect=', window.location.pathname))
        return
      }
      // console.log(error)
      // 我们的 errorThrower 抛出的错误。
      // if (opts?.skipErrorHandler) throw error;
      message.error('请求失败:'.concat(error.message));
    },
  },
  // 请求拦截器
  requestInterceptors: [(config: RequestOptions) => {
    // 拦截请求配置
    if(config.url !== '/api/login') {
      const currentUser = JSON.parse(localStorage.getItem("currentUser") || "{}")
      if (currentUser?.token) {
        return {...config, headers: {authorization: currentUser?.token}};
      } else {
        if(window.location.pathname !== loginPath) {
          history.push(loginPath.concat('?redirect=', window.location.pathname))
        }
        history.push(loginPath);
      }
    }
    return config
  }],

  // 响应拦截器
  responseInterceptors: [(response) => {
    // 拦截响应数据
    switch (response?.status) {
      case 200:
        break
      case 401:
        message.error('未登录或登录超时请重新登录');
        break
      case 403:
        message.error('用户无权限');
        break
      case 404:
        message.error('404 Not Found');
        break
      case 500:
        message.error(response.data || "系统错误")
        break
      default:
        break;
    }
    return response;
  }]
};

import { Settings as LayoutSettings } from '@ant-design/pro-components';


const Settings: LayoutSettings & {pwa?: boolean; logo?: string; } = {
  navTheme: 'light',
  // 拂晓蓝
  colorPrimary: '#1890ff',
  layout: 'mix',
  contentWidth: 'Fluid',
  fixedHeader: false,
  fixSiderbar: true,
  colorWeak: false,
  title: 'AutoOps',
  pwa: false,
  logo: 'https://kubernetes.io/images/wheel.svg',
  // logo: 'https://gw.alipayobjects.com/zos/rmsportal/KDpgvguMpGfqaHPjicRK.svg',
  iconfontUrl: '',
};

export default Settings;

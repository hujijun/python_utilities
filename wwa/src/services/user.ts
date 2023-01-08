// @ts-ignore
/* eslint-disable */
import { request } from '@umijs/max';

/** 登录接口 POST /api/login */
export async function login(body: API.LoginParams) {
  return request<API.CurrentUser>('/api/user/login', {method: 'POST', headers: {'Content-Type': 'application/json'},  data: body, skipErrorHandler: true});
}

export async function userList(body: { current?: number; pageSize?: number}) {
  return request<API.UserList>('/api/user/userList', {method: 'POST', headers: {'Content-Type': 'application/json'},  data: body, skipErrorHandler: true});
}

export async function updateUser(body: { [key: string]: any }) {
  return request<API.CurrentUser>('/api/user/updateUser', {method: 'POST', headers: {'Content-Type': 'application/json'},  data: body, skipErrorHandler: true});
}

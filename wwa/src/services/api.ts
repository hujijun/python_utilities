// @ts-ignore
/* eslint-disable */
import { request } from '@umijs/max';


/** 获取规则列表 GET /api/rule */
export async function rule(data: { current?: number; pageSize?: number}) {
  return request<API.RuleList>('/api/cmdb/modeList', {method: 'POST', data});
}

/** 新建规则 PUT /api/rule */
export async function updateRule(options?: { [key: string]: any }) {
  return request<API.RuleListItem>('/api/rule', {method: 'PUT', ...(options || {})});
}

/** 新建规则 POST /api/rule */
export async function addRule(options?: { [key: string]: any }) {
  return request<API.RuleListItem>('/api/rule', {method: 'POST', ...(options || {})});
}

/** 删除规则 DELETE /api/rule */
export async function removeRule(options?: { [key: string]: any }) {
  return request<Record<string, any>>('/api/rule', {method: 'DELETE', ...(options || {})});
}


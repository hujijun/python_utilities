// @ts-ignore
/* eslint-disable */
import { request } from '@umijs/max';


/** 新建资源模型 POST /api/cmdb/add-model */
export async function addModel(options?: { [key: string]: any }) {
  return request<API.RuleListItem>('/api/cmdb/add-model', {method: 'POST', ...(options || {})});
}


export async function modeList(options?: { [key: string]: any }) {
  return request<API.ModeList>('/api/cmdb/modeList', {method: 'POST', ...(options || {})});
}


export async function updateMode(options?: { [key: string]: any }) {
  return request<API.RuleListItem>('/api/cmdb/editMode', {method: 'POST', ...(options || {})});
}

export async function removeMode(options?: { [key: string]: any }) {
  return request<API.RuleListItem>('/api/cmdb/removeMode', {method: 'POST', ...(options || {})});
}


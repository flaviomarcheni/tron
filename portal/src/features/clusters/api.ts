import { api } from '../../shared/api'
import type { Cluster, ClusterCreate } from './types'

export const clustersApi = {
  list: async (organizationUuid: string): Promise<Cluster[]> => {
    if (!organizationUuid) {
      throw new Error('Organization UUID is required')
    }
    const response = await api.get<Cluster[]>(`/organizations/${organizationUuid}/clusters/`)
    return response.data
  },
  listByEnvironment: async (organizationUuid: string, environmentUuid: string): Promise<Cluster[]> => {
    if (!organizationUuid || !environmentUuid) {
      throw new Error('Organization UUID and environment UUID are required')
    }
    const response = await api.get<Cluster[]>(
      `/organizations/${organizationUuid}/environments/${environmentUuid}/clusters/`
    )
    return response.data
  },
  get: async (organizationUuid: string, uuid: string): Promise<Cluster> => {
    if (!organizationUuid) {
      throw new Error('Organization UUID is required')
    }
    const response = await api.get<Cluster>(`/organizations/${organizationUuid}/clusters/${uuid}`)
    return response.data
  },
  create: async (organizationUuid: string, data: ClusterCreate): Promise<Cluster> => {
    if (!organizationUuid) {
      throw new Error('Organization UUID is required')
    }
    const response = await api.post<Cluster>(`/organizations/${organizationUuid}/clusters/`, data)
    return response.data
  },
  update: async (organizationUuid: string, uuid: string, data: ClusterCreate): Promise<Cluster> => {
    if (!organizationUuid) {
      throw new Error('Organization UUID is required')
    }
    const response = await api.put<Cluster>(`/organizations/${organizationUuid}/clusters/${uuid}`, data)
    return response.data
  },
  delete: async (organizationUuid: string, uuid: string): Promise<void> => {
    if (!organizationUuid) {
      throw new Error('Organization UUID is required')
    }
    await api.delete(`/organizations/${organizationUuid}/clusters/${uuid}`)
  },
}

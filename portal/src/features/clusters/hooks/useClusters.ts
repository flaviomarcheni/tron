import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { clustersApi } from '../api'

export const useClusters = (organizationUuid: string | undefined) => {
  return useQuery({
    queryKey: ['clusters', organizationUuid],
    queryFn: () => {
      if (!organizationUuid) {
        throw new Error('Organization UUID is required to fetch clusters')
      }
      return clustersApi.list(organizationUuid)
    },
    enabled: !!organizationUuid,
  })
}

export const useClustersByEnvironment = (
  organizationUuid: string | undefined,
  environmentUuid: string | undefined
) => {
  return useQuery({
    queryKey: ['clusters', organizationUuid, 'environment', environmentUuid],
    queryFn: () => {
      if (!organizationUuid || !environmentUuid) {
        throw new Error('Organization UUID and environment UUID are required')
      }
      return clustersApi.listByEnvironment(organizationUuid, environmentUuid)
    },
    enabled: !!organizationUuid && !!environmentUuid,
  })
}

export const useCluster = (organizationUuid: string | undefined, uuid: string | undefined) => {
  return useQuery({
    queryKey: ['cluster', organizationUuid, uuid],
    queryFn: () => {
      if (!organizationUuid || !uuid) {
        throw new Error('Organization UUID and cluster UUID are required')
      }
      return clustersApi.get(organizationUuid, uuid)
    },
    enabled: !!organizationUuid && !!uuid,
  })
}

export const useCreateCluster = (organizationUuid: string | undefined) => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: import('../types').ClusterCreate) => {
      if (!organizationUuid) {
        throw new Error('Organization UUID is required')
      }
      return clustersApi.create(organizationUuid, data)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clusters', organizationUuid] })
    },
  })
}

export const useUpdateCluster = (organizationUuid: string | undefined) => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ uuid, data }: { uuid: string; data: import('../types').ClusterCreate }) => {
      if (!organizationUuid) {
        throw new Error('Organization UUID is required')
      }
      return clustersApi.update(organizationUuid, uuid, data)
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['clusters', organizationUuid] })
      queryClient.invalidateQueries({ queryKey: ['cluster', organizationUuid, variables.uuid] })
    },
  })
}

export const useDeleteCluster = (organizationUuid: string | undefined) => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (uuid: string) => {
      if (!organizationUuid) {
        throw new Error('Organization UUID is required')
      }
      return clustersApi.delete(organizationUuid, uuid)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clusters', organizationUuid] })
    },
  })
}

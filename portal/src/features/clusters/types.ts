import type { Environment } from '../environments/types'

export interface GatewayApiReference {
  namespace: string
  name: string
}

export interface GatewayReferences {
  public: GatewayApiReference
  private: GatewayApiReference
}

export interface GatewayApi {
  enabled: boolean
  resources: string[]
}

export interface GatewayFeatures {
  api: GatewayApi
  reference: GatewayReferences
}

export interface Cluster {
  uuid: string
  name: string
  api_address: string
  crossplane_available?: boolean
  environment_uuid: string
  environment?: Environment
  detail?: {
    status: string
    message?: {
      code: string
      message: string
    }
  }
  gateway?: GatewayFeatures
  created_at: string
  updated_at: string
}

export interface ClusterCreate {
  name: string
  api_address: string
  token: string
  environment_uuid: string
  crossplane_available?: boolean
  private_gateway_namespace?: string
  private_gateway_name?: string
  public_gateway_namespace?: string
  public_gateway_name?: string
}

export interface ClusterUpdate {
  name: string
  api_address: string
  token?: string
  environment_uuid: string
  crossplane_available?: boolean
}


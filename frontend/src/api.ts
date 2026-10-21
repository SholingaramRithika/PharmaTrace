import { useEffect, useState } from 'react'
const BASE = (import.meta.env.VITE_API_URL as string | undefined) ?? 'http://localhost:8000'
export class ApiError extends Error { constructor(public status: number, public code: string, msg: string) { super(msg) } }
export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  let r: Response
  try { r = await fetch(BASE + path, init) } catch { throw new ApiError(0, 'NETWORK', 'Cannot reach the backend API. Is it running on ' + BASE + '?') }
  const body = await r.json().catch(() => null)
  if (!r.ok) throw new ApiError(r.status, body?.error?.code ?? 'ERROR', body?.error?.message ?? r.statusText)
  return body as T
}
export function useApi<T>(path: string | null) {
  const [s, set] = useState<{ data?: T; error?: ApiError; loading: boolean }>({ loading: !!path })
  useEffect(() => {
    if (!path) { set({ loading: false }); return }
    let live = true; set(p => ({ ...p, loading: true, error: undefined }))
    api<T>(path).then(d => live && set({ data: d, loading: false })).catch(e => live && set({ error: e, loading: false }))
    return () => { live = false }
  }, [path])
  return s
}
export type GNode = { id: string; label: string; name: string; properties: Record<string, any> }
export type GEdge = { id: string; source: string; target: string; type: string; properties: Record<string, any> }
export type Graph = { nodes: GNode[]; edges: GEdge[]; truncated?: boolean }

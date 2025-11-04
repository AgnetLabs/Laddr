import { useQuery } from '@tanstack/react-query';
import api from '../api';
import type { Trace } from '../types';

export interface GroupedTrace {
  job_id: string;
  trace_count: number;
  agents: string[];
  start_time: string;
  end_time: string;
  traces: Trace[];
}

export const useTraces = (params?: { job_id?: string; agent_name?: string; limit?: number }) => {
  return useQuery({
    queryKey: ['traces', params?.job_id ?? null, params?.agent_name ?? null, params?.limit ?? 100],
    queryFn: async () => {
      const search = new URLSearchParams();
      if (params?.job_id) search.set('job_id', params.job_id);
      if (params?.agent_name) search.set('agent_name', params.agent_name);
      if (params?.limit) search.set('limit', String(params.limit));
      const qs = search.toString();
      const url = qs ? `/api/traces?${qs}` : '/api/traces';
      const { data } = await api.get<{ traces: Trace[] }>(url);
      return data.traces;
    },
  });
};

export const useGroupedTraces = (limit?: number) => {
  return useQuery({
    queryKey: ['grouped-traces', limit ?? 50],
    queryFn: async () => {
      const search = new URLSearchParams();
      if (limit) search.set('limit', String(limit));
      const qs = search.toString();
      const url = qs ? `/api/traces/grouped?${qs}` : '/api/traces/grouped';
      const { data } = await api.get<{ grouped_traces: GroupedTrace[] }>(url);
      return data.grouped_traces;
    },
    refetchInterval: 5000, // Refresh every 5 seconds
  });
};

export const useTrace = (traceId: string | null) => {
  return useQuery({
    enabled: !!traceId,
    queryKey: ['trace', traceId],
    queryFn: async () => {
      if (!traceId) return null as any;
      const { data } = await api.get<Trace>(`/api/traces/${traceId}`);
      return data;
    },
  });
};

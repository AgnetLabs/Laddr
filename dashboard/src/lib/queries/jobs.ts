import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../api';
import type { Job, PipelineRunRequest } from '../types';

export const useJobs = () => {
  return useQuery({
    queryKey: ['jobs'],
    queryFn: async () => {
      const { data } = await api.get<{ jobs: Job[]; limit: number; offset: number }>('/api/jobs');
      return data.jobs;
    },
    // Prefer event-driven updates or manual refresh; reduce polling
    staleTime: 5000,
    refetchOnWindowFocus: true,
  });
};

export const useJob = (jobId: string) => {
  return useQuery({
    queryKey: ['jobs', jobId],
    queryFn: async () => {
      const { data } = await api.get<Job>(`/api/jobs/${jobId}`);
      return data;
    },
    enabled: !!jobId,
    // Avoid tight polling; allow focus-based refetch
    staleTime: 3000,
    refetchOnWindowFocus: true,
  });
};

export const useRunPipeline = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (request: PipelineRunRequest) => {
      const { data } = await api.post<Job>('/api/jobs', {
        pipeline_name: request.pipeline_name,
        inputs: request.inputs || {}
      });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
  });
};

export const useReplayJob = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ jobId, reexecute = false }: { jobId: string; reexecute?: boolean }) => {
      const { data } = await api.post(`/api/jobs/${jobId}/replay`, { reexecute });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
  });
};

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../api';

export interface PromptExecution {
  prompt_id: string;
  prompt_name: string;
  status: 'pending' | 'running' | 'completed' | 'error' | 'failed' | 'canceled' | 'incomplete';
  created_at?: string;
  completed_at?: string;
  inputs?: Record<string, any>;
  outputs?: Record<string, any>;
  error?: string | null;
  token_usage?: {
    prompt_tokens?: number;
    completion_tokens?: number;
    total_tokens?: number;
    by_model?: Array<{
      provider?: string | null;
      model?: string | null;
      prompt_tokens?: number;
      completion_tokens?: number;
      total_tokens?: number;
      calls?: number;
    }>;
  };
}

export const usePrompts = (limit = 25) => {
  return useQuery({
    queryKey: ['prompts', { limit }],
    queryFn: async () => {
      const { data } = await api.get<{ prompts: PromptExecution[]; limit: number; offset: number }>(`/api/prompts?limit=${limit}`);
      return data.prompts;
    },
    staleTime: 5000,
    refetchOnWindowFocus: true,
  });
};

export const usePrompt = (promptId: string) => {
  return useQuery({
    queryKey: ['prompts', promptId],
    queryFn: async () => {
      const { data } = await api.get<PromptExecution>(`/api/prompts/${promptId}`);
      return data;
    },
    enabled: !!promptId,
    staleTime: 3000,
    refetchOnWindowFocus: true,
  });
};

export const useRunPrompt = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ 
      prompt_name, 
      inputs, 
      mode, 
      agents 
    }: { 
      prompt_name: string; 
      inputs?: Record<string, any>;
      mode?: string;
      agents?: string[];
    }) => {
      const { data } = await api.post<{ prompt_id: string; status: string; agent: string; mode?: string; agents?: string[] }>(
        '/api/prompts',
        { prompt_name, inputs: inputs || {}, mode, agents }
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prompts'] });
    },
  });
};

export const useCancelPrompt = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (promptId: string) => {
      const { data } = await api.post<{ ok: boolean; prompt_id: string; status: string }>(`/api/prompts/${promptId}/cancel`);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prompts'] });
    },
  });
};

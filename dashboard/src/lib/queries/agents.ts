import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../api';
import type { Agent, ChatRequest, ChatResponse } from '../types';

export const useAgents = () => {
  return useQuery({
    queryKey: ['agents'],
    queryFn: async () => {
      const { data } = await api.get<{ agents: Agent[] }>('/api/agents');
      return data.agents;
    },
  });
};

export const useAgent = (agentName: string) => {
  const agents = useAgents();
  
  return {
    ...agents,
    data: agents.data?.find(a => a.name === agentName),
  };
};

// Agent queue endpoint not available in v3.0 - removed
// Use job status and traces instead

export const useAgentChat = (agentName: string) => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (request: ChatRequest) => {
      const { data } = await api.post<ChatResponse>(
        `/api/agents/${agentName}/chat`,
        { message: request.message, wait: true, timeout: 30 }
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents', agentName] });
    },
  });
};

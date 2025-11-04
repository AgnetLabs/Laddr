import { useQuery } from '@tanstack/react-query';
import { api } from '../api';

interface ToolInfo {
  name: string;
  description: string;
  parameters: Record<string, any>;
}

interface AgentToolsResponse {
  agent: string;
  tools: ToolInfo[];
}

export function useAgentTools(agentName: string) {
  return useQuery<AgentToolsResponse>({
    queryKey: ['agentTools', agentName],
    queryFn: async () => {
      const response = await api.get(`/api/agents/${agentName}/tools`);
      return response.data;
    },
    enabled: !!agentName,
    staleTime: 30000, // Cache for 30 seconds
  });
}

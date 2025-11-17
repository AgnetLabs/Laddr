import { useQueries } from '@tanstack/react-query';
import { useAgents } from '../queries/agents';
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

/**
 * Hook to track loading state of all agents and their tools.
 * Returns true if any agents or their tools are still loading.
 */
export function useAgentsAndToolsLoading() {
  const { data: agents, isLoading: agentsLoading, isError: agentsError } = useAgents();

  // Fetch tools for all agents in parallel
  const toolsQueries = useQueries({
    queries: (agents || []).map((agent) => ({
      queryKey: ['agentTools', agent.name],
      queryFn: async () => {
        const response = await api.get<AgentToolsResponse>(`/api/agents/${agent.name}/tools`);
        return response.data;
      },
      enabled: !!agents && agents.length > 0,
      staleTime: 30000,
      retry: 2, // Retry up to 2 times
      retryDelay: 1000, // Wait 1s between retries
    })),
  });

  const toolsLoading = toolsQueries.some((query) => query.isLoading);
  const toolsError = toolsQueries.some((query) => query.isError);
  const toolsFetching = toolsQueries.some((query) => query.isFetching && !query.data);

  // Loading if:
  // - Agents are loading
  // - Any tools are loading (initial load)
  // - Any tools are fetching without data (first fetch, not refetch)
  const isLoading = agentsLoading || toolsLoading || toolsFetching;

  // Error if agents failed or any tools failed
  const hasError = agentsError || toolsError;

  return {
    isLoading,
    hasError,
    agentsLoading,
    toolsLoading,
    agentsCount: agents?.length || 0,
    loadedToolsCount: toolsQueries.filter((q) => q.isSuccess).length,
  };
}


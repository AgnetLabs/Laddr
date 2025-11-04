import { useQuery } from '@tanstack/react-query';
import api from '../api';
import type { HealthStatus } from '../types';

export const useHealth = () => {
  return useQuery({
    queryKey: ['health'],
    queryFn: async () => {
      const { data } = await api.get<HealthStatus>('/api/health');
      return data;
    },
    refetchInterval: 30000, // Refetch every 30 seconds
  });
};

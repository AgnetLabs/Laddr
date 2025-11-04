import { useQuery } from '@tanstack/react-query';
import api from '../api';
import type { SystemMetrics } from '../types';

export const useMetrics = () => {
  return useQuery({
    queryKey: ['metrics'],
    queryFn: async () => {
      const { data } = await api.get<SystemMetrics>('/api/metrics');
      return data;
    },
    refetchInterval: 10000, // Refetch every 10 seconds
  });
};

import { useState, useEffect, useRef } from 'react';
import { Terminal, Download, Trash2, Play, Pause, Search, RefreshCw } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';
import { getWebSocketBaseUrl } from '../lib/config';

interface ContainerInfo {
  id: string;
  name: string;
  service_name: string;
  project_name: string;
  type: 'api' | 'worker' | 'infrastructure' | 'other';
  status: string;
  image: string;
  created: string;
}

interface LogLine {
  timestamp: string;
  message: string;
}

interface ContainerLogs {
  container: string;
  container_id: string;
  status: string;
  logs: LogLine[];
  total: number;
}

export default function Logs() {
  const [selectedContainer, setSelectedContainer] = useState<string>('');
  const [autoScroll, setAutoScroll] = useState(true);
  const [tail, setTail] = useState(200);
  const [searchTerm, setSearchTerm] = useState('');
  const logsEndRef = useRef<HTMLDivElement>(null);
  const logsContainerRef = useRef<HTMLDivElement>(null);
  const [wsLogs, setWsLogs] = useState<LogLine[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [typeFilter, setTypeFilter] = useState<string>('all');

  // Fetch list of containers
  const { data: containersData, refetch: refetchContainers } = useQuery({
    queryKey: ['containers'],
    queryFn: async () => {
      const response = await api.get('/api/logs/containers');
      return response.data as { containers: ContainerInfo[]; total: number };
    },
    refetchInterval: 10000, // Refresh every 10 seconds
  });

  // Fetch logs for selected container
  const { data: logsData, refetch: refetchLogs, isLoading: isLoadingLogs } = useQuery({
    queryKey: ['container-logs', selectedContainer, tail],
    queryFn: async () => {
      if (!selectedContainer) return null;
      const response = await api.get(`/api/logs/containers/${selectedContainer}`, {
        params: { tail, timestamps: true },
      });
      return response.data as ContainerLogs;
    },
    enabled: !!selectedContainer && !isStreaming,
    refetchInterval: isStreaming ? false : 5000, // Refresh every 5 seconds when not streaming
  });

  // WebSocket for real-time logs
  useEffect(() => {
    if (!selectedContainer || !isStreaming) {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      return;
    }

    const wsBaseUrl = getWebSocketBaseUrl();
    // Remove trailing slash if present
    const baseUrl = wsBaseUrl.endsWith('/') ? wsBaseUrl.slice(0, -1) : wsBaseUrl;
    const wsUrl = `${baseUrl}/ws/logs/${selectedContainer}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('WebSocket connected for logs');
      setWsLogs([]);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'log') {
        setWsLogs((prev) => [...prev, data.data]);
      } else if (data.type === 'connected') {
        console.log('Connected to container:', data.data);
      } else if (data.type === 'error') {
        console.error('WebSocket error:', data.data.error);
        setIsStreaming(false);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setIsStreaming(false);
    };

    ws.onclose = () => {
      console.log('WebSocket closed');
    };

    return () => {
      ws.close();
    };
  }, [selectedContainer, isStreaming]);

  // Auto-scroll to bottom
  useEffect(() => {
    if (autoScroll && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logsData, wsLogs, autoScroll]);

  const displayLogs = isStreaming ? wsLogs : (logsData?.logs || []);
  
  // Filter logs by search term
  const filteredLogs = searchTerm
    ? displayLogs.filter((log) =>
        log.message.toLowerCase().includes(searchTerm.toLowerCase())
      )
    : displayLogs;

  // Filter containers by type
  const filteredContainers = containersData?.containers.filter((c) => {
    if (typeFilter === 'all') return true;
    return c.type === typeFilter;
  }) || [];

  const downloadLogs = () => {
    const logsText = filteredLogs
      .map((log) => `${log.timestamp} ${log.message}`)
      .join('\n');
    const blob = new Blob([logsText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${selectedContainer || 'container'}-logs.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const clearLogs = () => {
    if (isStreaming) {
      setWsLogs([]);
    } else {
      refetchLogs();
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'running':
        return 'text-green-400 bg-green-400/10';
      case 'exited':
        return 'text-red-400 bg-red-400/10';
      case 'paused':
        return 'text-yellow-400 bg-yellow-400/10';
      default:
        return 'text-gray-400 bg-gray-400/10';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'api':
        return '🌐';
      case 'worker':
        return '⚙️';
      case 'infrastructure':
        return '🗄️';
      default:
        return '📦';
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'api':
        return 'text-blue-400 bg-blue-400/10';
      case 'worker':
        return 'text-purple-400 bg-purple-400/10';
      case 'infrastructure':
        return 'text-gray-400 bg-gray-400/10';
      default:
        return 'text-gray-500 bg-gray-500/10';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    if (!timestamp) return '';
    try {
      // Format: 2024-01-01T12:00:00.000000000Z -> 12:00:00.000
      const timePart = timestamp.split('T')[1];
      if (!timePart) return timestamp;
      const timeWithMs = timePart.split('Z')[0];
      return timeWithMs.substring(0, 12); // HH:MM:SS.mmm
    } catch {
      return timestamp;
    }
  };

  return (
    <div className="space-y-6 bg-[#191A1A] min-h-screen p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-[#1F2121] rounded-lg">
            <Terminal className="w-7 h-7 text-[#1FB8CD]" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Container Logs</h1>
            <p className="text-sm text-gray-400">
              View logs from Docker containers • API & Workers
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {selectedContainer && (
            <>
              <button
                onClick={() => setIsStreaming(!isStreaming)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                  isStreaming
                    ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30 border border-red-500/50'
                    : 'bg-green-500/20 text-green-400 hover:bg-green-500/30 border border-green-500/50'
                }`}
              >
                {isStreaming ? (
                  <>
                    <Pause className="w-4 h-4" />
                    Stop Stream
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4" />
                    Live Stream
                  </>
                )}
              </button>
              <button
                onClick={downloadLogs}
                disabled={filteredLogs.length === 0}
                className="flex items-center gap-2 px-4 py-2 bg-[#1F2121] border border-gray-800 rounded-lg text-sm text-gray-400 hover:text-white hover:border-[#1FB8CD] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Download className="w-4 h-4" />
                Download
              </button>
              <button
                onClick={clearLogs}
                disabled={filteredLogs.length === 0}
                className="flex items-center gap-2 px-4 py-2 bg-[#1F2121] border border-gray-800 rounded-lg text-sm text-gray-400 hover:text-white hover:border-[#1FB8CD] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Trash2 className="w-4 h-4" />
                Clear
              </button>
            </>
          )}
          <button
            onClick={() => refetchContainers()}
            className="flex items-center gap-2 px-4 py-2 bg-[#1F2121] border border-gray-800 rounded-lg text-sm text-gray-400 hover:text-white hover:border-[#1FB8CD] transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Containers List */}
        <div className="lg:col-span-1">
          <div className="bg-[#1F2121] rounded-lg border border-gray-800 overflow-hidden">
            <div className="bg-[#191A1A] px-4 py-3 border-b border-gray-800">
              <h2 className="text-sm font-medium text-white">Containers</h2>
              <p className="text-xs text-gray-500 mt-1">
                {filteredContainers.length} of {containersData?.total || 0}
              </p>
            </div>

            {/* Type Filter */}
            <div className="p-3 border-b border-gray-800">
              <select
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                className="w-full bg-[#191A1A] border border-gray-800 rounded px-2 py-1.5 text-xs text-white focus:outline-none focus:border-[#1FB8CD]"
              >
                <option value="all">All Types</option>
                <option value="api">API</option>
                <option value="worker">Workers</option>
                <option value="infrastructure">Infrastructure</option>
              </select>
            </div>

            <div className="max-h-[600px] overflow-y-auto">
              {filteredContainers.length === 0 ? (
                <div className="p-4 text-center text-gray-500 text-sm">
                  No containers found
                </div>
              ) : (
                <div className="divide-y divide-gray-800">
                  {filteredContainers.map((container) => (
                    <button
                      key={container.id}
                      onClick={() => {
                        setSelectedContainer(container.name);
                        setIsStreaming(false);
                        setSearchTerm('');
                      }}
                      className={`w-full p-3 text-left hover:bg-[#252525] transition-colors ${
                        selectedContainer === container.name
                          ? 'bg-[#1FB8CD]/10 border-l-2 border-[#1FB8CD]'
                          : ''
                      }`}
                    >
                      <div className="flex items-start gap-2">
                        <span className="text-lg">{getTypeIcon(container.type)}</span>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <span
                              className={`text-xs px-1.5 py-0.5 rounded font-medium ${getTypeColor(
                                container.type
                              )}`}
                            >
                              {container.type}
                            </span>
                            <span
                              className={`text-xs px-1.5 py-0.5 rounded font-medium ${getStatusColor(
                                container.status
                              )}`}
                            >
                              {container.status}
                            </span>
                          </div>
                          <p className="text-sm text-white font-medium truncate">
                            {container.service_name}
                          </p>
                          <p className="text-xs text-gray-500 truncate">
                            {container.name}
                          </p>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Logs Display */}
        <div className="lg:col-span-3">
          <div className="bg-[#1F2121] rounded-lg border border-gray-800 overflow-hidden">
            {/* Logs Header */}
            <div className="bg-[#191A1A] px-4 py-3 border-b border-gray-800">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-sm font-medium text-white">
                    {selectedContainer || 'No container selected'}
                  </span>
                  {isStreaming && (
                    <span className="flex items-center gap-1.5 text-xs text-green-400">
                      <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                      Live
                    </span>
                  )}
                </div>
                <span className="text-xs text-gray-500">
                  {filteredLogs.length} lines
                  {searchTerm && ` (filtered from ${displayLogs.length})`}
                </span>
              </div>
            </div>

            {/* Logs Controls */}
            {selectedContainer && (
              <div className="bg-[#1A1B1B] px-4 py-2 border-b border-gray-800 flex items-center gap-4">
                {!isStreaming && (
                  <>
                    <label className="text-xs text-gray-400">Lines:</label>
                    <select
                      value={tail}
                      onChange={(e) => setTail(Number(e.target.value))}
                      className="bg-[#191A1A] border border-gray-800 rounded px-2 py-1 text-xs text-white focus:outline-none focus:border-[#1FB8CD]"
                    >
                      <option value={50}>50</option>
                      <option value={100}>100</option>
                      <option value={200}>200</option>
                      <option value={500}>500</option>
                      <option value={1000}>1000</option>
                    </select>
                  </>
                )}

                <div className="flex-1">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                    <input
                      type="text"
                      placeholder="Search logs..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="w-full bg-[#191A1A] border border-gray-800 rounded pl-9 pr-3 py-1.5 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-[#1FB8CD]"
                    />
                  </div>
                </div>

                <label className="flex items-center gap-2 text-xs text-gray-400">
                  <input
                    type="checkbox"
                    checked={autoScroll}
                    onChange={(e) => setAutoScroll(e.target.checked)}
                    className="rounded border-gray-800 bg-[#191A1A] text-[#1FB8CD] focus:ring-[#1FB8CD] focus:ring-offset-0"
                  />
                  Auto-scroll
                </label>
              </div>
            )}

            {/* Logs Content */}
            <div
              ref={logsContainerRef}
              className="h-[600px] overflow-y-auto bg-[#0A0A0A] font-mono text-xs terminal-scroll"
            >
              {isLoadingLogs ? (
                <div className="flex items-center justify-center h-full text-gray-500">
                  Loading logs...
                </div>
              ) : filteredLogs.length === 0 ? (
                <div className="flex items-center justify-center h-full text-gray-500">
                  {selectedContainer
                    ? searchTerm
                      ? 'No logs match your search'
                      : 'No logs available'
                    : 'Select a container to view logs'}
                </div>
              ) : (
                <div className="p-4">
                  {filteredLogs.map((log, index) => (
                    <div
                      key={index}
                      className="flex gap-3 py-0.5 hover:bg-[#1F2121]/30 group"
                    >
                      {log.timestamp && (
                        <span className="text-gray-600 select-none shrink-0 font-medium">
                          {formatTimestamp(log.timestamp)}
                        </span>
                      )}
                      <span className="text-gray-300 break-all leading-relaxed">
                        {log.message}
                      </span>
                    </div>
                  ))}
                  <div ref={logsEndRef} />
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

import { useHealth } from '../lib/queries/health';
import { useMetrics } from '../lib/queries/metrics';
import { useAgents } from '../lib/queries/agents';
import { CheckCircle, Users, Briefcase, Clock, Search, ChevronLeft, ChevronRight } from 'lucide-react';
import { useState } from 'react';

export default function Dashboard() {
  const { data: health, isLoading: healthLoading } = useHealth();
  const { data: metrics, isLoading: metricsLoading } = useMetrics();
  const { data: agents } = useAgents();
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [showColumns, setShowColumns] = useState(false);
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

  // Mock data for the table - replace with actual data
  const tableData =
    agents?.map((agent) => ({
      agent: agent.name,
      description: agent.role,
      toolsCount: agent.tools?.length || 0,
      traceCount: agent.trace_count || 0,
      lastExecuted: agent.last_executed || 'Never',
    })) || [];

  // Sort by lastExecuted
  const sortedData = [...tableData].sort((a, b) => {
    // Handle 'Never' case
    if (a.lastExecuted === 'Never' && b.lastExecuted === 'Never') return 0;
    if (a.lastExecuted === 'Never') return sortOrder === 'asc' ? 1 : -1;
    if (b.lastExecuted === 'Never') return sortOrder === 'asc' ? -1 : 1;
    
    const dateA = new Date(a.lastExecuted).getTime();
    const dateB = new Date(b.lastExecuted).getTime();
    return sortOrder === 'asc' ? dateA - dateB : dateB - dateA;
  });

  const itemsPerPage = 5;
  const totalPages = Math.ceil(sortedData.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const paginatedData = sortedData.slice(startIndex, startIndex + itemsPerPage);

  const toggleSortOrder = () => {
    setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
  };

  // Format timestamp for display
  const formatTimestamp = (timestamp: string) => {
    if (timestamp === 'Never') return 'Never';
    try {
      const date = new Date(timestamp);
      return date.toLocaleString('en-US', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false,
      });
    } catch {
      return timestamp;
    }
  };

  return (
    <div className=" space-y-6 bg-[#191A1A]">
      {/* Stats Grid - Top Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-[#1F2121] rounded-lg p-6 border border-gray-800">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium text-white bg-[#171717] px-2 py-1 rounded">System Status</h3>
            <CheckCircle className="w-5 h-5 text-cyan-400" />
          </div>
          <p className="text-3xl font-semibold text-white">
            {healthLoading ? '...' : health?.status === 'ok' ? 'Healthy' : 'Unknown'}
          </p>
        </div>

        <div className="bg-[#1F2121] rounded-lg p-6 border border-gray-800">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium text-white bg-[#171717] px-2 py-1 rounded">Active Agents</h3>
            <Users className="w-5 h-5 text-cyan-400" />
          </div>
          <p className="text-3xl font-semibold text-white">
            {metricsLoading ? '...' : metrics?.active_agents_count ?? agents?.length ?? 0}
          </p>
        </div>

        <div className="bg-[#1F2121] rounded-lg p-6 border border-gray-800">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium text-white bg-[#171717] px-2 py-1 rounded">Total Jobs</h3>
            <Briefcase className="w-5 h-5 text-cyan-400" />
          </div>
          <p className="text-3xl font-semibold text-white">
            {metricsLoading ? '...' : metrics?.total_jobs ?? 0}
          </p>
        </div>

        <div className="bg-[#1F2121] rounded-lg p-6 border border-gray-800">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium text-white bg-[#171717] px-2 py-1 rounded">Average Runtime</h3>
            <Clock className="w-5 h-5 text-[#1FB8CD]" />
          </div>
          <p className="text-3xl font-semibold text-white">
            {metricsLoading ? '...' : `${((metrics?.avg_latency_ms ?? 0) / 1000).toFixed(1)}s`}
          </p>
        </div>
      </div>

      {/* Second Row - Additional Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-[#1F2121] rounded-lg p-6 border border-gray-800">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium text-white bg-[#171717] px-2 py-1 rounded">Tool Calls</h3>
            <Briefcase className="w-5 h-5 text-[#1FB8CD]" />
          </div>
          <p className="text-3xl font-semibold text-white">
            {metricsLoading ? '...' : metrics?.tool_calls ?? 0}
          </p>
        </div>

        <div className="bg-[#1F2121] rounded-lg p-6 border border-gray-800">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium text-white bg-[#171717] px-2 py-1 rounded">Cache Hits</h3>
            <CheckCircle className="w-5 h-5 text-[#1FB8CD]" />
          </div>
          <p className="text-3xl font-semibold text-white">
            {metricsLoading ? '...' : metrics?.cache_hits ?? 0}
          </p>
        </div>

        <div className="bg-[#1F2121] rounded-lg p-6 border border-gray-800">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium text-white bg-[#171717] px-2 py-1 rounded">Total Tokens</h3>
            <Clock className="w-5 h-5 text-[#1FB8CD]" />
          </div>
          <p className="text-3xl font-semibold text-white">
            {metricsLoading ? '...' : (metrics?.total_tokens ?? 0).toLocaleString()}
          </p>
        </div>

        <div className="bg-[#1F2121] rounded-lg p-6 border border-gray-800">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium text-white bg-[#171717] px-2 py-1 rounded">Completed Jobs</h3>
            <CheckCircle className="w-5 h-5 text-green-400" />
          </div>
          <p className="text-3xl font-semibold text-white">
            {metricsLoading ? '...' : metrics?.completed_jobs ?? 0}
          </p>
        </div>
      </div>

      {/* Search Bar */}
      <div className="flex items-center justify-between gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-[#1FB8CD]" />
          <input
            type="text"
            placeholder="Find Agent"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-[#1f1f1f] border border-gray-800 rounded-lg pl-10 pr-4 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-[#1FB8CD]"
          />
        </div>
        <div className="relative">
          <button
            onClick={() => setShowColumns(!showColumns)}
            className="flex items-center gap-2 px-4 py-2 bg-[#1f1f1f] border border-gray-800 rounded-lg text-sm text-gray-400 hover:text-white hover:border-[#1FB8CD] transition-colors"
          >
            Columns
            <ChevronRight className={`w-4 h-4 transition-transform ${showColumns ? 'rotate-90' : ''}`} />
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="bg-[#1F2121] rounded-lg border border-gray-800 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-800">
                <th className="text-left px-6 py-4 text-sm font-medium text-gray-400">Agent</th>
                <th className="text-left px-6 py-4 text-sm font-medium text-gray-400">Description</th>
                <th className="text-left px-6 py-4 text-sm font-medium text-gray-400">Tools Count</th>
                <th className="text-left px-6 py-4 text-sm font-medium text-gray-400">Trace Count</th>
                <th
                  onClick={toggleSortOrder}
                  className="text-left px-6 py-4 text-sm font-medium text-gray-400 cursor-pointer select-none"
                >
                  <div className="flex items-center gap-2">
                    Last Executed
                    <div className="flex flex-col gap-0.5">
                      <ChevronRight
                        className={`w-3 h-3 -rotate-90 ${
                          sortOrder === 'asc' ? 'text-[#1FB8CD]' : 'text-gray-600'
                        }`}
                      />
                      <ChevronRight
                        className={`w-3 h-3 rotate-90 ${
                          sortOrder === 'desc' ? 'text-[#1FB8CD]' : 'text-gray-600'
                        }`}
                      />
                    </div>
                  </div>
                </th>
              </tr>
            </thead>
            <tbody>
              {paginatedData.map((row, idx) => (
                <tr key={idx} className="border-b border-gray-800 hover:bg-[#252525] transition-colors">
                  <td className="px-6 py-4 text-sm text-gray-300">{row.agent}</td>
                  <td className="px-6 py-4 text-sm text-gray-400">{row.description}</td>
                  <td className="px-6 py-4 text-sm text-gray-300">{row.toolsCount}</td>
                  <td className="px-6 py-4 text-sm text-gray-300">{row.traceCount}</td>
                  <td className="px-6 py-4 text-sm text-gray-400">{formatTimestamp(row.lastExecuted)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pagination - moved outside table */}
      <div className="flex justify-end items-center gap-2 px-6 py-4">
        <button
          onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
          disabled={currentPage === 1}
          className="flex items-center gap-1 px-3 py-1.5 text-sm text-gray-400 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <ChevronLeft className="w-4 h-4" />
          Previous
        </button>

        {[...Array(Math.min(totalPages, 5))].map((_, idx) => {
          const pageNum = idx + 1;
          return (
            <button
              key={pageNum}
              onClick={() => setCurrentPage(pageNum)}
              className={`px-3 py-1.5 text-sm rounded transition-colors ${
                currentPage === pageNum
                  ? 'bg-cyan-400 text-black font-medium'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              {pageNum}
            </button>
          );
        })}

        {totalPages > 5 && (
          <>
            <span className="text-gray-400">...</span>
            <button
              onClick={() => setCurrentPage(totalPages)}
              className="px-3 py-1.5 text-sm text-gray-400 hover:text-white transition-colors"
            >
              {totalPages}
            </button>
          </>
        )}

        <button
          onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
          disabled={currentPage === totalPages}
          className="flex items-center gap-1 px-3 py-1.5 text-sm text-gray-400 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Next
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

import { useState } from 'react';
import { useGroupedTraces, useTrace } from '../lib/queries/traces';
import { GitBranch, ChevronDown, ChevronRight, Copy, Check } from 'lucide-react';
import { format } from 'date-fns';

export default function Traces() {
  const [expandedJobs, setExpandedJobs] = useState<Set<string>>(new Set());
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  
  const { data: groupedTraces, isLoading } = useGroupedTraces(50);
  const { data: selectedTrace } = useTrace(selectedId);

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  const toggleJob = (jobId: string) => {
    const newExpanded = new Set(expandedJobs);
    if (newExpanded.has(jobId)) {
      newExpanded.delete(jobId);
    } else {
      newExpanded.add(jobId);
    }
    setExpandedJobs(newExpanded);
  };

  const calculateDuration = (startTime: string, endTime: string) => {
    const start = new Date(startTime).getTime();
    const end = new Date(endTime).getTime();
    const duration = end - start;
    
    if (duration < 1000) return `${duration}ms`;
    if (duration < 60000) return `${(duration / 1000).toFixed(1)}s`;
    return `${(duration / 60000).toFixed(1)}m`;
  };

  const calculateJobStats = (traces: any[]) => {
    const toolCalls = traces.filter(t => t.event_type === 'tool_call').length;
    
    // Calculate total tokens from llm_usage events
    const totalTokens = traces.reduce((sum, t) => {
      // Check for llm_usage event type (this is where token usage is tracked)
      if (t.event_type === 'llm_usage' && t.payload?.total_tokens) {
        return sum + t.payload.total_tokens;
      }
      return sum;
    }, 0);
    
    // Calculate cost estimate (using typical GPT-4 pricing as example)
    // Input: $0.03/1K tokens, Output: $0.06/1K tokens (average ~$0.045/1K)
    const estimatedCost = (totalTokens / 1000) * 0.045;
    
    return { toolCalls, totalTokens, estimatedCost };
  };

  const getEventTypeColor = (eventType: string) => {
    const colors: Record<string, string> = {
      'agent_start': 'text-blue-400',
      'agent_end': 'text-green-400',
      'tool_call': 'text-yellow-400',
      'tool_result': 'text-purple-400',
      'delegation': 'text-orange-400',
      'error': 'text-red-400',
    };
    return colors[eventType] || 'text-gray-400';
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-gray-400">Loading traces...</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">Traces</h1>
        <div className="flex items-center gap-4">
          <div className="text-xs text-gray-600 italic">
            * Cost estimates are approximate
          </div>
          <div className="text-sm text-gray-500">
            {groupedTraces?.length || 0} job runs
          </div>
        </div>
      </div>

      <div className="space-y-2">
        {groupedTraces && groupedTraces.length > 0 ? (
          groupedTraces.map((group) => {
            const isExpanded = expandedJobs.has(group.job_id);
            const stats = calculateJobStats(group.traces);
            const jobDuration = calculateDuration(group.start_time, group.end_time);
            
            return (
              <div key={group.job_id} className="bg-[#1a1a1a] rounded-md border border-gray-800 overflow-hidden hover:border-blue-500/30 transition-colors">
                {/* Job Header */}
                <div
                  className="px-5 py-3.5 cursor-pointer hover:bg-blue-500/5 transition-colors"
                  onClick={() => toggleJob(group.job_id)}
                >
                  <div className="flex items-center justify-between gap-4">
                    {/* Left side: ID and expand icon */}
                    <div className="flex items-center gap-3">
                      <div className="text-purple-500">
                        {isExpanded ? (
                          <ChevronDown className="w-4 h-4" />
                        ) : (
                          <ChevronRight className="w-4 h-4" />
                        )}
                      </div>
                      <div className="flex items-center gap-4">
                        <code className="text-sm font-medium text-white">
                          {group.job_id.slice(0, 8)}
                        </code>
                        <div className="flex items-center gap-3">
                          {group.agents.map((agent, idx) => (
                            <span key={idx} className="px-2 py-0.5 bg-cyan-400/15 text-cyan-300 text-xs rounded border border-cyan-400/30">
                              {agent}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* Right side: Stats */}
                    <div className="flex items-center gap-6 text-xs">
                      <div className="flex items-center gap-3 text-gray-400">
                        <span className="font-medium text-white">{stats.toolCalls}</span>
                        <span>tools</span>
                      </div>
                      <div className="flex items-center gap-3 text-gray-400">
                        <span className="font-medium text-white">{stats.totalTokens.toLocaleString()}</span>
                        <span>${stats.estimatedCost.toFixed(2)}</span>
                      </div>
                      <div className="text-gray-500">
                        {format(new Date(group.end_time), 'M/d/yyyy, h:mm:ss a')}
                      </div>
                      <div className="flex items-center gap-2 text-gray-400">
                        <span className="font-medium text-white">{jobDuration}</span>
                      </div>
                      <div className="px-2.5 py-1 bg-cyan-400/15 rounded text-cyan-300 border border-cyan-400/30">
                        {group.trace_count} events
                      </div>
                    </div>
                  </div>
                </div>

                {/* Traces List */}
                {isExpanded && (
                  <div className="border-t border-gray-800">
                    <table className="w-full">
                      <thead className="bg-gray-900/50">
                        <tr>
                          <th className="px-5 py-2 text-left text-xs font-medium text-gray-500">Event</th>
                          <th className="px-5 py-2 text-left text-xs font-medium text-gray-500">Agent</th>
                          <th className="px-5 py-2 text-left text-xs font-medium text-gray-500">Details</th>
                          <th className="px-5 py-2 text-left text-xs font-medium text-gray-500">Time</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-800">
                        {group.traces.map((trace) => (
                          <tr
                            key={trace.id}
                            className="hover:bg-gray-900/30 cursor-pointer"
                            onClick={() => setSelectedId(String(trace.id))}
                          >
                            <td className="px-5 py-3">
                              <div className="flex items-center gap-2">
                                <GitBranch className={`w-4 h-4 ${getEventTypeColor(trace.event_type)}`} />
                                <span className="text-sm text-white">{trace.event_type}</span>
                              </div>
                            </td>
                            <td className="px-5 py-3">
                              <span className="text-sm text-gray-400">{trace.agent_name || '-'}</span>
                            </td>
                            <td className="px-5 py-3">
                              <div className="text-xs text-gray-500">
                                {trace.event_type === 'tool_call' && trace.payload?.tool && (
                                  <span>Tool: {trace.payload.tool}</span>
                                )}
                                {trace.event_type === 'tool_result' && trace.payload?.tool && (
                                  <span>
                                    {trace.payload.tool}
                                    {trace.payload.status && ` - ${trace.payload.status}`}
                                  </span>
                                )}
                                {trace.event_type === 'delegation' && trace.payload?.target_agent && (
                                  <span>→ {trace.payload.target_agent}</span>
                                )}
                              </div>
                            </td>
                            <td className="px-5 py-3">
                              <span className="text-xs text-gray-600">
                                {format(new Date(trace.timestamp), 'HH:mm:ss.SSS')}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            );
          })
        ) : (
          <div className="bg-[#1a1a1a] rounded-md border border-gray-800 px-6 py-12 text-center">
            <p className="text-gray-500">No traces found</p>
          </div>
        )}
      </div>

      {/* Trace Detail Modal */}
      {selectedId && selectedTrace && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" onClick={() => setSelectedId(null)}>
          <div className="bg-gray-900 border border-gray-700 rounded-lg w-full max-w-3xl overflow-hidden" onClick={(e) => e.stopPropagation()}>
            <div className="px-6 py-4 border-b border-gray-700 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-white">Trace Details</h2>
              <button
                onClick={() => setSelectedId(null)}
                className="text-gray-400 hover:text-white"
                aria-label="Close"
              >
                ✕
              </button>
            </div>
            <div className="p-6 space-y-4 max-h-[70vh] overflow-auto">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-xs text-gray-400">Trace ID</div>
                  <div className="text-sm text-white break-all">{selectedTrace.id}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-400">Job ID</div>
                  <div className="text-sm text-white break-all">{selectedTrace.job_id || '-'}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-400">Agent</div>
                  <div className="text-sm text-white">{selectedTrace.agent_name || '-'}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-400">Event Type</div>
                  <div className="text-sm text-white">{selectedTrace.event_type}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-400">Timestamp</div>
                  <div className="text-sm text-white">{format(new Date(selectedTrace.timestamp), 'MMM d, yyyy HH:mm:ss')}</div>
                </div>
              </div>
              {/* Friendly payload renderer for known event types */}
              {selectedTrace.event_type === 'tool_result' ? (
                <div className="space-y-3">
                  <div className="text-xs text-gray-400">Tool</div>
                  <div className="text-sm text-white">
                    {selectedTrace.payload?.tool || '-'}
                    <span className="ml-2 text-xs text-gray-400">{typeof selectedTrace.payload?.duration_ms === 'number' ? `${selectedTrace.payload.duration_ms} ms` : ''}</span>
                  </div>
                  {(selectedTrace.payload?.result_preview || selectedTrace.payload?.result) && (
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <div className="text-xs text-gray-400">Result</div>
                        <button
                          onClick={() => copyToClipboard(
                            typeof selectedTrace.payload.result === 'string'
                              ? selectedTrace.payload.result
                              : (selectedTrace.payload.result_preview || JSON.stringify(selectedTrace.payload.result, null, 2))
                          )}
                          className="flex items-center gap-1 px-2 py-1 text-xs text-gray-400 hover:text-white bg-gray-700 hover:bg-gray-600 rounded transition-colors"
                          title="Copy to clipboard"
                        >
                          {copied ? (
                            <>
                              <Check className="w-3 h-3" />
                              Copied!
                            </>
                          ) : (
                            <>
                              <Copy className="w-3 h-3" />
                              Copy
                            </>
                          )}
                        </button>
                      </div>
                      <pre className="bg-gray-800 text-gray-200 text-xs p-4 rounded-md overflow-auto border border-gray-700 whitespace-pre-wrap">
                        {typeof selectedTrace.payload.result === 'string'
                          ? selectedTrace.payload.result
                          : (selectedTrace.payload.result_preview || JSON.stringify(selectedTrace.payload.result, null, 2))}
                      </pre>
                    </div>
                  )}
                  {/* Raw payload fallback */}
                  <details className="mt-2">
                    <summary className="text-xs text-gray-400 cursor-pointer">Raw payload</summary>
                    <pre className="bg-gray-800 text-gray-200 text-xs p-4 rounded-md overflow-auto border border-gray-700">
                      {JSON.stringify(selectedTrace.payload, null, 2)}
                    </pre>
                  </details>
                </div>
              ) : (
                <div>
                  <div className="text-xs text-gray-400 mb-2">Payload</div>
                  <pre className="bg-gray-800 text-gray-200 text-xs p-4 rounded-md overflow-auto border border-gray-700">
                    {JSON.stringify(selectedTrace.payload, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

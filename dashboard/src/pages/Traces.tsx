import { useState } from 'react';
import { useGroupedTraces, useTrace } from '../lib/queries/traces';
import { GitBranch, ChevronDown, ChevronRight, Copy, Check } from 'lucide-react';
import { format } from 'date-fns';

export default function Traces() {
  const [expandedJobs, setExpandedJobs] = useState<Set<string>>(new Set());
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [activeTab, setActiveTab] = useState("Payload");
  
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
    <div className="space-y-4 flex flex-col">
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
      <div className="flex flex-row gap-6 items-start">
        <div className="flex-1 max-h-[80vh] overflow-y-auto pr-2 space-y-2">
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
        {/* Trace Detail Sidebar */}
        {selectedId && selectedTrace && (
          <div className="w-[38%] border bg-[#1a1a1a] border-gray-800 rounded-lg overflow-hidden flex flex-col shadow-xl transition-all duration-300 ease-out">
            
            {/* Header */}
            <div className="p-4 border-b border-gray-800 flex items-center justify-between bg-[#1a1a1a]">
              <h2 className="text-base font-semibold text-white">Trace Details</h2>
              <button
                onClick={() => setSelectedId(null)}
                className="text-gray-400 hover:text-white transition-colors"
              >
                ✕
              </button>
            </div>

            {/* Metadata Section */}
            <div className="px-6 py-4 border-b border-gray-800 grid grid-cols-2 gap-y-3 text-sm">
              <div>
                <div className="text-xs text-gray-400">Trace ID</div>
                <div className="text-gray-200 break-all">{selectedTrace.id}</div>
              </div>
              <div>
                <div className="text-xs text-gray-400">Job ID</div>
                <div className="text-gray-200 break-all">
                  {selectedTrace.job_id || "-"}
                </div>
              </div>
              <div>
                <div className="text-xs text-gray-400">Event Type</div>
                <div className="text-gray-300">{selectedTrace.event_type}</div>
              </div>
            </div>

            {/* Tabs */}
            <div className="flex border-b border-gray-800 items-center justify-between px-4 bg-[#1a1a1a]">
              <div className="flex flex-1">
                {["Result", "Response", "Payload", "Raw"].map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={`flex-1 py-2 text-sm font-medium transition-colors ${
                      activeTab === tab
                        ? "text-cyan-400 border-b-2 border-cyan-400"
                        : "text-gray-400 hover:text-white"
                    }`}
                  >
                    {tab}
                  </button>
                ))}
              </div>
            </div>

            {/* Tab Content */}
            <div className="flex-1 overflow-y-auto p-6 text-sm">
              {/* Result Tab */}
              {activeTab === "Result" && (
                selectedTrace.payload?.result ? (
                  <div className="relative bg-[#171717] border border-gray-700 rounded-md p-3 text-xs text-gray-200 whitespace-pre-wrap overflow-auto">
                    <button
                      onClick={() =>
                        copyToClipboard(
                          typeof selectedTrace.payload.result === "string"
                            ? selectedTrace.payload.result
                            : JSON.stringify(selectedTrace.payload.result, null, 2)
                        )
                      }
                      className="absolute top-2 right-2 text-gray-400 hover:text-white transition"
                    >
                      {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                    </button>
                    {typeof selectedTrace.payload.result === "string"
                      ? selectedTrace.payload.result
                      : JSON.stringify(selectedTrace.payload.result, null, 2)}
                  </div>
                ) : (
                  <div className="text-gray-500 italic text-center py-8">
                    No result found for this trace
                  </div>
                )
              )}

              {/* Response Tab */}
              {activeTab === "Response" && (
                selectedTrace.payload?.response ? (
                  <div className="relative bg-[#171717] border border-gray-700 rounded-md p-3 text-xs text-gray-200 whitespace-pre-wrap overflow-auto">
                    <button
                      onClick={() =>
                        copyToClipboard(
                          typeof selectedTrace.payload.response === "string"
                            ? selectedTrace.payload.response
                            : JSON.stringify(selectedTrace.payload.response, null, 2)
                        )
                      }
                      className="absolute top-2 right-2 text-gray-400 hover:text-white transition"
                    >
                      {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                    </button>
                    {typeof selectedTrace.payload.response === "string"
                      ? selectedTrace.payload.response
                      : JSON.stringify(selectedTrace.payload.response, null, 2)}
                  </div>
                ) : (
                  <div className="text-gray-500 italic text-center py-8">
                    No response found for this trace
                  </div>
                )
              )}

              {/* Payload Tab */}
              {activeTab === "Payload" && (
                <div className="relative bg-[#171717] border border-gray-700 rounded-md p-3 text-xs text-gray-200 overflow-auto">
                  <button
                    onClick={() =>
                      copyToClipboard(JSON.stringify(selectedTrace.payload, null, 2))
                    }
                    className="absolute top-2 right-2 text-gray-400 hover:text-white transition"
                  >
                    {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                  </button>
                  <pre>{JSON.stringify(selectedTrace.payload, null, 2)}</pre>
                </div>
              )}

              {/* Raw Tab */}
              {activeTab === "Raw" && (
                <div className="relative bg-[#171717] border border-gray-700 rounded-md p-3 text-xs text-gray-200 overflow-auto">
                  <button
                    onClick={() =>
                      copyToClipboard(JSON.stringify(selectedTrace, null, 2))
                    }
                    className="absolute top-2 right-2 text-gray-400 hover:text-white transition"
                  >
                    {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                  </button>
                  <pre>{JSON.stringify(selectedTrace, null, 2)}</pre>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

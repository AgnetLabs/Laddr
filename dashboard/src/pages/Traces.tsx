import { useState } from 'react';
import { useGroupedTraces, useTrace } from '../lib/queries/traces';
import { GitBranch, ChevronDown, ChevronRight, Copy, Check } from 'lucide-react';
import { format } from 'date-fns';

export default function Traces() {
  const [expandedJobs, setExpandedJobs] = useState<Set<string>>(new Set());
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [activeTab, setActiveTab] = useState('Payload');
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());

  const { data: groupedTraces, isLoading } = useGroupedTraces(50);
  const { data: selectedTrace } = useTrace(selectedId);

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  const toggleJob = (jobId: string) => {
    const next = new Set(expandedJobs);
    if (next.has(jobId)) next.delete(jobId);
    else next.add(jobId);
    setExpandedJobs(next);
  };

  const toggleNode = (nodeId: string) => {
    const next = new Set(expandedNodes);
    if (next.has(nodeId)) next.delete(nodeId);
    else next.add(nodeId);
    setExpandedNodes(next);
  };

  const calculateDuration = (startTime: string, endTime: string) => {
    const start = new Date(startTime).getTime();
    const end = new Date(endTime).getTime();
    const ms = Math.max(0, end - start);
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    return `${(ms / 60000).toFixed(1)}m`;
  };

  const calculateJobStats = (traces: any[]) => {
    const toolCalls = traces.filter((t) => t.event_type === 'tool_call').length;
    let totalInputTokens = 0;
    let totalOutputTokens = 0;
    let totalTokens = 0;
    let estimatedCost = 0;

    const MODEL_PRICING = { inputPerToken: 0.003 / 10000, outputPerToken: 0.025 / 10000 };

    traces.forEach((t) => {
      if (t.event_type === 'llm_usage' && t.payload) {
        const inT = Number(t.payload.prompt_tokens || 0);
        const outT = Number(t.payload.completion_tokens || 0);
        totalInputTokens += inT;
        totalOutputTokens += outT;
        totalTokens += inT + outT;
        estimatedCost += inT * MODEL_PRICING.inputPerToken + outT * MODEL_PRICING.outputPerToken;
      }
    });

    return { toolCalls, totalTokens, totalInputTokens, totalOutputTokens, estimatedCost };
  };

  const buildTraceTree = (traces: any[]) => {
    type Node = { event: any; children: Node[] };
    const roots: Node[] = [];
    const stack: Node[] = [];

    const isOpen = (t: string) => t.endsWith('_start') || t === 'tool_call' || t === 'agent_start' || t === 'task_start';
    const isClose = (t: string) => t.endsWith('_complete') || t === 'tool_result' || t === 'agent_end' || t === 'task_complete';

    traces.forEach((trace) => {
      const type = trace.event_type;
      const node: Node = { event: trace, children: [] };

      if (isOpen(type)) stack.push(node);
      else if (isClose(type)) {
        const last = stack.pop();
        if (last) {
          last.children.push(node);
          const parent = stack[stack.length - 1];
          if (parent) parent.children.push(last);
          else roots.push(last);
        } else roots.push(node);
      } else if (type === 'llm_usage' || type === 'autonomous_think') {
        const parent = stack[stack.length - 1];
        if (parent) parent.children.push(node);
        else roots.push(node);
      } else {
        const parent = stack[stack.length - 1];
        if (parent) parent.children.push(node);
        else roots.push(node);
      }
    });

    while (stack.length) {
      const leftover = stack.pop()!;
      const parent = stack[stack.length - 1];
      if (parent) parent.children.push(leftover);
      else roots.push(leftover);
    }

    return roots;
  };

  const getEventTypeColor = (eventType: string) => {
    const colors: Record<string, string> = {
      agent_start: 'text-blue-400',
      agent_end: 'text-green-400',
      tool_call: 'text-yellow-400',
      tool_result: 'text-purple-400',
      delegation: 'text-orange-400',
      error: 'text-red-400',
    };
    return colors[eventType] || 'text-gray-400';
  };

  if (isLoading) return (
    <div className="flex items-center justify-center h-64">
      <p className="text-gray-400">Loading traces...</p>
    </div>
  );

  return (
    <div className="space-y-4 flex flex-col">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">Traces</h1>
        <div className="flex items-center gap-4">
          <div className="text-xs text-gray-600 italic">* Cost estimates are approximate</div>
          <div className="text-sm text-gray-500">{groupedTraces?.length || 0} job runs</div>
        </div>
      </div>

      <div className="flex flex-row gap-6 items-start">
        <div className="flex-1 max-h-[80vh] overflow-y-auto pr-2 space-y-2">
          {groupedTraces && groupedTraces.length > 0 ? (
            groupedTraces.map((group) => {
              const isExpanded = expandedJobs.has(group.job_id);
              const stats = calculateJobStats(group.traces || []);
              const jobDuration = calculateDuration(group.start_time, group.end_time);

              const tree = buildTraceTree(group.traces || []);

              const renderNode = (node: any, depth = 0): JSX.Element => {
                const ev = node.event;
                const nodeError = (() => {
                  return (
                    ev?.payload?.error || ev?.metadata?.error || ev?.error || ev?.message || (typeof ev?.status === 'string' && ev.status === 'error') || null
                  );
                })();
                const nodeId = String(ev.id ?? `${ev.event_type}-${Math.random()}`);
                const hasChildren = node.children && node.children.length > 0;
                const isNodeExpanded = expandedNodes.has(nodeId);
                return (
                  <div key={nodeId} className="mb-2">
                    <div className="flex flex-col">
                      <div
                        onClick={() => setSelectedId(String(ev.id))}
                        className={`flex items-center gap-3 cursor-pointer hover:bg-gray-900/20 rounded px-4 py-3 transition-colors ${depth === 0 ? '' : 'bg-gray-900/5'}`}
                        style={{ paddingLeft: `${depth * 24}px` }}
                      >
                        <div className="w-6 flex items-center justify-center">
                          {hasChildren ? (
                            <button
                              onClick={(e) => { e.stopPropagation(); toggleNode(nodeId); }}
                              className="p-1 rounded hover:bg-gray-800/30"
                            >
                              {isNodeExpanded ? <ChevronDown className="w-4 h-4 text-gray-300" /> : <ChevronRight className="w-4 h-4 text-gray-500" />}
                            </button>
                          ) : (
                            <div className="w-4 h-4" />
                          )}
                        </div>

                        <div className="w-6 flex-shrink-0">
                          <GitBranch className={`w-4 h-4 ${getEventTypeColor(ev.event_type)}`} />
                        </div>

                        <div className="flex-1">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                              <div className="text-sm font-medium text-white">{ev.event_type}</div>
                              <div className="text-xs text-gray-400">{ev.agent_name || '-'}</div>
                            </div>
                            <div className="text-xs text-gray-500">{format(new Date(ev.timestamp), 'HH:mm:ss.SSS')}</div>
                          </div>

                          <div className="text-xs text-gray-400 mt-2 flex items-center gap-3">
                            {ev.event_type === 'tool_call' && ev.payload?.tool && <span className="px-2 py-0.5 bg-gray-800 rounded">Tool: {ev.payload.tool}</span>}
                            {ev.event_type === 'tool_result' && ev.payload?.tool && (
                              <span className="px-2 py-0.5 bg-gray-800 rounded">{ev.payload.tool}{ev.payload.status ? ` - ${ev.payload.status}` : ''}</span>
                            )}
                            {ev.event_type === 'delegation' && ev.payload?.target_agent && <span className="px-2 py-0.5 bg-gray-800 rounded">→ {ev.payload.target_agent}</span>}
                            {ev.event_type === 'llm_usage' && (
                              <>
                                <span className="px-2 py-0.5 bg-cyan-400/10 text-cyan-300 rounded font-medium">{ev.payload?.model || 'model'}</span>
                                <span className="text-gray-400">{ev.payload?.prompt_tokens ?? 0} in</span>
                                <span className="text-gray-400">/ {ev.payload?.completion_tokens ?? 0} out</span>
                              </>
                            )}
                            {nodeError && (
                              <span className="px-2 py-0.5 bg-red-800 text-red-300 rounded">{nodeError}</span>
                            )}
                          </div>
                        </div>
                      </div>

                      {hasChildren && isNodeExpanded && (
                        <div className="mt-1">
                          {node.children.map((c: any) => renderNode(c, depth + 1))}
                        </div>
                      )}
                    </div>
                  </div>
                );
              };

              return (
                <div key={group.job_id} className="bg-[#1a1a1a] rounded-md border border-gray-800 overflow-hidden hover:border-blue-500/30 transition-colors">
                  <div className="px-5 py-3.5 cursor-pointer hover:bg-blue-500/5 transition-colors" onClick={() => toggleJob(group.job_id)}>
                    <div className="flex items-center justify-between gap-4">
                      <div className="flex items-center gap-3">
                        <div className="text-purple-500">{isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}</div>
                        <div className="flex items-center gap-4">
                          <code className="text-sm font-medium text-white">{group.job_id.slice(0, 8)}</code>
                          <div className="flex items-center gap-3">{group.agents?.map((agent: string, idx: number) => <span key={idx} className="px-2 py-0.5 bg-cyan-400/15 text-cyan-300 text-xs rounded border border-cyan-400/30">{agent}</span>)}</div>
                        </div>
                      </div>

                      <div className="flex items-center gap-6 text-xs">
                        <div className="flex items-center gap-3 text-gray-400"><span className="font-medium text-white">{stats.toolCalls}</span><span>tools</span></div>
                        <div className="flex items-center gap-3 text-gray-400"><span className="font-medium text-white">{stats.totalTokens.toLocaleString()}</span><span>${stats.estimatedCost.toFixed(4)}</span></div>
                        <div className="text-gray-500">{format(new Date(group.end_time), 'M/d/yyyy, h:mm:ss a')}</div>
                        <div className="flex items-center gap-2 text-gray-400"><span className="font-medium text-white">{jobDuration}</span></div>
                        <div className="px-2.5 py-1 bg-cyan-400/15 rounded text-cyan-300 border border-cyan-400/30">{group.trace_count} events</div>
                      </div>
                    </div>
                  </div>

                  {isExpanded && (
                    <div className="border-t border-gray-800 p-4">
                      <div>{tree.map((n: any) => renderNode(n, 0))}</div>
                    </div>
                  )}
                </div>
              );
            })
          ) : (
            <div className="bg-[#1a1a1a] rounded-md border border-gray-800 px-6 py-12 text-center"><p className="text-gray-500">No traces found</p></div>
          )}
        </div>

        {selectedId && selectedTrace && (
          <div className="w-[38%] border bg-[#1a1a1a] border-gray-800 rounded-lg overflow-hidden flex flex-col shadow-xl transition-all duration-300 ease-out">
            <div className="p-4 border-b border-gray-800 flex items-center justify-between bg-[#1a1a1a]"><h2 className="text-base font-semibold text-white">Trace Details</h2><button onClick={() => setSelectedId(null)} className="text-gray-400 hover:text-white transition-colors">✕</button></div>

            <div className="px-6 py-4 border-b border-gray-800 grid grid-cols-2 gap-y-3 text-sm">
              <div><div className="text-xs text-gray-400">Trace ID</div><div className="text-gray-200 break-all">{selectedTrace.id}</div></div>
              <div><div className="text-xs text-gray-400">Job ID</div><div className="text-gray-200 break-all">{selectedTrace.job_id || '-'}</div></div>
              <div><div className="text-xs text-gray-400">Event Type</div><div className="text-gray-300">{selectedTrace.event_type}</div></div>
            </div>

            <div className="flex border-b border-gray-800 items-center justify-between px-4 bg-[#1a1a1a]"><div className="flex flex-1">{['Result','Response','Payload','Raw'].map((tab) => (<button key={tab} onClick={() => setActiveTab(tab)} className={`flex-1 py-2 text-sm font-medium transition-colors ${activeTab === tab ? 'text-cyan-400 border-b-2 border-cyan-400' : 'text-gray-400 hover:text-white'}`}>{tab}</button>))}</div></div>

            <div className="flex-1 overflow-y-auto p-6 text-sm">
              {activeTab === 'Result' && (() => {
                // Normalize multiple possible fields where an error/result may live
                const resultCandidates = [
                  selectedTrace?.payload?.result,
                  selectedTrace?.output,
                  selectedTrace?.result,
                  selectedTrace?.payload?.response,
                  selectedTrace?.metadata?.error,
                  selectedTrace?.payload?.error,
                  selectedTrace?.error,
                ];

                const resultVal = resultCandidates.find((v) => v !== undefined && v !== null);
                if (resultVal) {
                  const text = typeof resultVal === 'string' ? resultVal : JSON.stringify(resultVal, null, 2);
                  return (
                    <div className="relative bg-[#171717] border border-gray-700 rounded-md p-3 text-xs text-gray-200 whitespace-pre-wrap overflow-auto">
                      <button onClick={() => copyToClipboard(text)} className="absolute top-2 right-2 text-gray-400 hover:text-white transition">{copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}</button>
                      {text}
                    </div>
                  );
                }
                return (<div className="text-gray-500 italic text-center py-8">No result found for this trace</div>);
              })()}

              {activeTab === 'Response' && (selectedTrace.payload?.response ? (
                <div className="relative bg-[#171717] border border-gray-700 rounded-md p-3 text-xs text-gray-200 whitespace-pre-wrap overflow-auto">
                  <button onClick={() => copyToClipboard(typeof selectedTrace.payload.response === 'string' ? selectedTrace.payload.response : JSON.stringify(selectedTrace.payload.response, null, 2))} className="absolute top-2 right-2 text-gray-400 hover:text-white transition">{copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}</button>
                  {typeof selectedTrace.payload.response === 'string' ? selectedTrace.payload.response : JSON.stringify(selectedTrace.payload.response, null, 2)}
                </div>
              ) : (<div className="text-gray-500 italic text-center py-8">No response found for this trace</div>))}

              {activeTab === 'Payload' && (
                <div className="relative bg-[#171717] border border-gray-700 rounded-md p-3 text-xs text-gray-200 overflow-auto">
                  <button onClick={() => copyToClipboard(JSON.stringify(selectedTrace.payload, null, 2))} className="absolute top-2 right-2 text-gray-400 hover:text-white transition">{copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}</button>
                  <pre>{JSON.stringify(selectedTrace.payload, null, 2)}</pre>
                </div>
              )}

              {activeTab === 'Raw' && (
                <div className="relative bg-[#171717] border border-gray-700 rounded-md p-3 text-xs text-gray-200 overflow-auto">
                  <button onClick={() => copyToClipboard(JSON.stringify(selectedTrace, null, 2))} className="absolute top-2 right-2 text-gray-400 hover:text-white transition">{copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}</button>
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

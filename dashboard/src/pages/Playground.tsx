import { useState } from "react";
import { format } from 'date-fns';
import {
  Play,
  ChevronDown,
  ChevronRight,
  Clock,
  Zap,
  Database,
  Activity,
  Code,
  Brain,
  X,
  StopCircle,
  GitBranch,
  
} from "lucide-react";
import { useAgents } from "../lib/queries/agents";
import {
  useRunPlayground,
  useCancelPlayground,
} from "../lib/queries/playground.ts";
import { usePlaygroundTraces } from "../lib/hooks/useWebSocket";
interface Span {
  id: number;
  name: string;
  type: "agent" | "tool" | "llm" | "reasoning" | "event";
  start_time: string;
  agent: string;
  event_type: string;
  input?: any;
  output?: any;
  metadata: {
    duration_ms?: number;
    tokens?: number;
    cost?: number;
    [key: string]: any;
  };
  children: Span[];
}

interface SpanRowProps {
  span: Span;
  depth: number;
  isExpanded: boolean;
  onToggle: () => void;
}

const fmtNumber = (v: any) => {
  if (v == null) return "";
  return typeof v === "number" && !isNaN(v) ? v.toLocaleString() : String(v);
};

function SpanRow({ span, depth, isExpanded, onToggle }: SpanRowProps) {
  const hasChildren = span.children && span.children.length > 0;

  // Get icon based on span type
  const getIcon = () => {
    switch (span.type) {
      case "agent":
        return <Activity className="w-4 h-4 text-cyan-400" />;
      case "tool":
        return <Code className="w-4 h-4 text-purple-400" />;
      case "llm":
        return <Brain className="w-4 h-4 text-green-400" />;
      case "reasoning":
        return <Database className="w-4 h-4 text-yellow-400" />;
      default:
        return <div className="w-4 h-4 rounded-full bg-gray-600" />;
    }
  };

  // Format duration
  const formatDuration = (ms?: number) => {
    if (!ms) return null;
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  return (
    <div className="border-b border-gray-800">
      {/* Main row */}
      <div
        className="flex items-center gap-3 py-3 px-4 hover:bg-[#1F2121] cursor-pointer transition-colors"
        style={{ paddingLeft: `${depth * 24 + 16}px` }}
        onClick={onToggle}
      >
        {/* Expand/collapse icon */}
        <div className="w-4 h-4 flex-shrink-0">
          {hasChildren &&
            (isExpanded ? (
              <ChevronDown className="w-4 h-4 text-gray-400" />
            ) : (
              <ChevronRight className="w-4 h-4 text-gray-400" />
            ))}
        </div>

        {/* Type icon */}
        <div className="flex-shrink-0">{getIcon()}</div>

        {/* Name */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-white truncate">
              {span.name}
            </span>
            <span className="text-xs text-gray-500">{span.type}</span>
          </div>
        </div>

        {/* Metrics */}
        <div className="flex items-center gap-4 flex-shrink-0">
          {span.metadata.tokens && (
            <div className="flex items-center gap-1.5 text-xs text-gray-400">
              <Zap className="w-3.5 h-3.5" />
              <span>{fmtNumber(span.metadata.tokens)}</span>
            </div>
          )}
          {span.metadata.duration_ms && (
            <div className="flex items-center gap-1.5 text-xs text-gray-400">
              <Clock className="w-3.5 h-3.5" />
              <span>{formatDuration(span.metadata.duration_ms)}</span>
            </div>
          )}
          {span.metadata.cost && (
            <div className="text-xs text-gray-400">
              ${span.metadata.cost.toFixed(4)}
            </div>
          )}
        </div>
      </div>

      {/* Expanded details */}
      {isExpanded && (
        <div
          className="bg-[#0D0E0E] px-4 py-3 border-t border-gray-800"
          style={{ paddingLeft: `${depth * 24 + 16}px` }}
        >
          <div className="space-y-3 text-sm">
            {/* For llm_usage - show provider, model, token details */}
            {span.event_type === "llm_usage" && span.metadata && (
              <div>
                <div className="text-xs font-semibold text-gray-400 mb-1">
                  LLM Usage
                </div>
                <div className="bg-[#191A1A] rounded p-2 text-xs border border-gray-800 space-y-1">
                  {span.metadata.provider && (
                    <div>
                      <span className="text-gray-500">Provider:</span>
                      <span className="ml-2 text-gray-300">
                        {span.metadata.provider}
                      </span>
                    </div>
                  )}
                  {span.metadata.model && (
                    <div>
                      <span className="text-gray-500">Model:</span>
                      <span className="ml-2 text-gray-300">
                        {span.metadata.model}
                      </span>
                    </div>
                  )}
                  {span.metadata.prompt_tokens !== undefined && (
                    <div>
                      <span className="text-gray-500">Prompt Tokens:</span>
                      <span className="ml-2 text-gray-300">
                        {fmtNumber(span.metadata.prompt_tokens)}
                      </span>
                    </div>
                  )}
                  {span.metadata.completion_tokens !== undefined && (
                    <div>
                      <span className="text-gray-500">Completion Tokens:</span>
                      <span className="ml-2 text-gray-300">
                        {fmtNumber(span.metadata.completion_tokens)}
                      </span>
                    </div>
                  )}
                  {span.metadata.total_tokens !== undefined && (
                    <div>
                      <span className="text-gray-500">Total Tokens:</span>
                      <span className="ml-2 text-cyan-400 font-semibold">
                        {fmtNumber(span.metadata.total_tokens)}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* For autonomous_think - show response and timing */}
            {span.event_type === "autonomous_think" && span.metadata && (
              <>
                {span.metadata.response && (
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <div className="text-xs font-semibold text-gray-400">
                        Reasoning Response
                        <span className="ml-2 text-gray-500 font-normal">
                          (
                          {typeof span.metadata.response === "string"
                            ? span.metadata.response.length.toLocaleString()
                            : JSON.stringify(
                                span.metadata.response
                              ).length.toLocaleString()}{" "}
                          chars)
                        </span>
                      </div>
                      <button
                        onClick={() => {
                          const text =
                            typeof span.metadata.response === "string"
                              ? span.metadata.response
                              : JSON.stringify(span.metadata.response, null, 2);
                          navigator.clipboard.writeText(text);
                        }}
                        className="text-xs px-2 py-1 bg-[#1FB8CD]/10 hover:bg-[#1FB8CD]/20 text-[#1FB8CD] rounded border border-[#1FB8CD]/30 transition-colors"
                      >
                        Copy
                      </button>
                    </div>
                    <div className="bg-[#191A1A] rounded p-3 border border-gray-800 max-h-96 overflow-y-auto">
                      <pre className="text-xs text-gray-300 whitespace-pre-wrap break-words">
                        {typeof span.metadata.response === "string"
                          ? span.metadata.response
                          : JSON.stringify(span.metadata.response, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}
                {span.metadata.iteration !== undefined && (
                  <div className="bg-[#191A1A] rounded p-2 text-xs border border-gray-800 mt-2">
                    <span className="text-gray-500">Iteration:</span>
                    <span className="ml-2 text-gray-300">
                      {span.metadata.iteration}
                    </span>
                    {span.metadata.duration_ms && (
                      <>
                        <span className="text-gray-500 ml-4">Duration:</span>
                        <span className="ml-2 text-gray-300">
                          {(span.metadata.duration_ms / 1000).toFixed(2)}s
                        </span>
                      </>
                    )}
                  </div>
                )}
              </>
            )}

            {/* Standard Input (for other event types) */}
            {span.event_type !== "llm_usage" &&
              span.event_type !== "autonomous_think" &&
              span.input &&
              Object.keys(span.input).length > 0 && (
                <div>
                  <div className="text-xs font-semibold text-gray-400 mb-1">
                    Input
                  </div>
                  <pre className="bg-[#191A1A] rounded p-2 text-xs text-gray-300 overflow-x-auto border border-gray-800">
                    {JSON.stringify(span.input, null, 2)}
                  </pre>
                </div>
              )}

            {/* Standard Output (for other event types) */}
            {span.event_type !== "llm_usage" &&
              span.event_type !== "autonomous_think" &&
              span.output && (
                <div>
                  <div className="text-xs font-semibold text-gray-400 mb-1">
                    Output
                  </div>
                  <pre className="bg-[#191A1A] rounded p-2 text-xs text-gray-300 overflow-x-auto border border-gray-800">
                    {JSON.stringify(span.output, null, 2)}
                  </pre>
                </div>
              )}

            {/* Metadata */}
            <div>
              <div className="text-xs font-semibold text-gray-400 mb-1">
                Metadata
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-gray-500">Agent:</span>
                  <span className="ml-2 text-gray-300">{span.agent}</span>
                </div>
                <div>
                  <span className="text-gray-500">Event:</span>
                  <span className="ml-2 text-gray-300">{span.event_type}</span>
                </div>
                <div>
                  <span className="text-gray-500">Time:</span>
                  <span className="ml-2 text-gray-300">
                    {new Date(span.start_time).toLocaleTimeString()}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Render children */}
      {isExpanded && hasChildren && (
        <div>
          {span.children.map((child) => (
            <SpanTreeNode key={child.id} span={child} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  );
}

function SpanTreeNode({ span, depth }: { span: Span; depth: number }) {
  const [isExpanded, setIsExpanded] = useState(false);
  return (
    <SpanRow
      span={span}
      depth={depth}
      isExpanded={isExpanded}
      onToggle={() => setIsExpanded(!isExpanded)}
    />
  );
}

export default function Playground() {
  const { data: agents } = useAgents();
  const runPlayground = useRunPlayground();
  const cancelPlayground = useCancelPlayground();

  // Form state
  const [promptText, setPromptText] = useState("");
  const [mode, setMode] = useState<"single" | "sequential">("single");
  const [selectedAgent, setSelectedAgent] = useState("");
  const [selectedAgents, setSelectedAgents] = useState<string[]>([]);

  // Live trace state
  const [activePlaygroundId, setActivePlaygroundId] = useState<string | null>(
    null
  );
  const [showTraces, setShowTraces] = useState(false);
  const { traces, isConnected, isComplete } =
    usePlaygroundTraces(activePlaygroundId);

  // Set default agent when agents load
  useState(() => {
    if (agents && agents.length > 0 && !selectedAgent) {
      setSelectedAgent(agents[0].name);
    }
  });

  const toggleAgentSelection = (agentName: string) => {
    if (selectedAgents.includes(agentName)) {
      setSelectedAgents(selectedAgents.filter((a) => a !== agentName));
    } else {
      setSelectedAgents([...selectedAgents, agentName]);
    }
  };

  const handleRun = async () => {
    if (!promptText.trim()) return;

    try {
      // Clear previous traces before starting new run
      setActivePlaygroundId(null);
      setShowTraces(false);

      const payload = { query: promptText };
      const reqBody =
        mode === "sequential"
          ? {
              prompt_name: selectedAgents[0] || "coordinator",
              inputs: payload,
              mode: "sequential",
              agents: selectedAgents,
            }
          : {
              prompt_name: selectedAgent || "coordinator",
              inputs: payload,
              mode: "single",
            };

      const res = await runPlayground.mutateAsync(reqBody);
      if ((res as any)?.prompt_id) {
        // Small delay to ensure traces are cleared before new ones start
        setTimeout(() => {
          setActivePlaygroundId((res as any).prompt_id as string);
          setShowTraces(true);
        }, 100);
      }
    } catch (err) {
      console.error("Failed to run playground:", err);
    }
  };

  const handleCancel = async () => {
    if (!activePlaygroundId) return;
    try {
      await cancelPlayground.mutateAsync(activePlaygroundId);
    } catch (err) {
      console.error("Failed to cancel playground:", err);
    }
  };

  const handleCloseTraces = () => {
    setShowTraces(false);
    // Don't clear activePlaygroundId immediately to allow traces to finish loading
    if (isComplete) {
      setTimeout(() => setActivePlaygroundId(null), 500);
    }
  };

  // Extract spans from traces (WebSocket sends hierarchical structure)
  const spans: Span[] =
    traces.length > 0 && traces[0].spans ? traces[0].spans : [];

  // Recursively calculate total tokens from all spans
  const calculateTotalTokens = (spanList: Span[]): number => {
    return spanList.reduce((sum, span) => {
      const spanTokens = span.metadata?.tokens || 0;
      const childTokens = calculateTotalTokens(span.children || []);
      return sum + spanTokens + childTokens;
    }, 0);
  };

  // Calculate total duration: time from first span to last span
  const calculateTotalDuration = (spanList: Span[]): number => {
    if (spanList.length === 0) return 0;

    try {
      // Get first span's start time
      const firstSpan = spanList[0];
      const firstStartTime = new Date(firstSpan.start_time).getTime();

      // Get last span's start time
      const lastSpan = spanList[spanList.length - 1];
      const lastStartTime = new Date(lastSpan.start_time).getTime();

      // Return the difference
      return lastStartTime - firstStartTime;
    } catch (e) {
      return 0;
    }
  };

  const totalTokens = calculateTotalTokens(spans);
  const totalDuration = calculateTotalDuration(spans);

  // --- Traces-style tree builder (adapted from Traces.tsx) ---
  type TraceNode = { event: any; children: TraceNode[] };

  const buildTraceTree = (events: any[] = []): TraceNode[] => {
    const roots: TraceNode[] = [];
    const stack: TraceNode[] = [];

    const isOpen = (t: string) =>
      t.endsWith("_start") ||
      t === "tool_call" ||
      t === "agent_start" ||
      t === "task_start";
    const isClose = (t: string) =>
      t.endsWith("_complete") ||
      t === "tool_result" ||
      t === "agent_end" ||
      t === "task_complete";

    for (const ev of events) {
      const type = ev.event_type;
      const node: TraceNode = { event: ev, children: [] };

      if (isOpen(type)) {
        stack.push(node);
      } else if (isClose(type)) {
        const last = stack.pop();
        if (last) {
          last.children.push(node);
          const parent = stack[stack.length - 1];
          if (parent) parent.children.push(last);
          else roots.push(last);
        } else {
          roots.push(node);
        }
      } else if (type === "llm_usage" || type === "autonomous_think") {
        const parent = stack[stack.length - 1];
        if (parent) parent.children.push(node);
        else roots.push(node);
      } else {
        const parent = stack[stack.length - 1];
        if (parent) parent.children.push(node);
        else roots.push(node);
      }
    }

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
      agent_start: "text-blue-400",
      agent_end: "text-green-400",
      tool_call: "text-yellow-400",
      tool_result: "text-purple-400",
      delegation: "text-orange-400",
      error: "text-red-400",
    };
    return colors[eventType] || "text-gray-400";
  };

  function TraceNodeRow({
    node,
    depth = 0,
  }: {
    node: TraceNode;
    depth?: number;
  }) {
    // Start collapsed by default — show details only when user clicks (old architecture)
  const [isExpanded, setIsExpanded] = useState<boolean>(false);
    const ev = node.event;
    const hasChildren = node.children && node.children.length > 0;

    return (
      <div className="mb-2">
        <div className="flex flex-col">
          <div
            className={`flex items-center gap-3 rounded px-4 py-3 transition-colors ${
              depth === 0 ? "" : "bg-gray-900/5"
            }`}
            style={{ paddingLeft: `${depth * 24}px` }}
          >
            <div className="w-6 flex items-center justify-center">
              {/* Chevron controls showing/hiding the details only. Children (trace structure) are always visible below. */}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setIsExpanded(!isExpanded);
                }}
                className="p-1 rounded hover:bg-gray-800/30"
                aria-label={isExpanded ? "Collapse details" : "Expand details"}
              >
                {isExpanded ? (
                  <ChevronDown className="w-4 h-4 text-gray-300" />
                ) : (
                  <ChevronRight className="w-4 h-4 text-gray-500" />
                )}
              </button>
            </div>

            <div className="w-6 flex-shrink-0">
              <GitBranch
                className={`w-4 h-4 ${getEventTypeColor(ev.event_type)}`}
              />
            </div>

                        <div className="flex-1">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                              <div className="text-sm font-medium text-white">{ev.event_type}</div>
                              <div className="text-xs text-gray-400">{ev.agent || '-'}</div>
                            </div>
                            <div className="text-xs text-gray-500">{ev.start_time ? format(new Date(ev.start_time), 'HH:mm:ss.SSS') : ''}</div>
                          </div>

                          <div className="text-xs text-gray-400 mt-2 flex items-center gap-3">
                            {ev.event_type === 'tool_call' && (ev.payload?.tool || ev.metadata?.tool || ev.metadata?.params?.tool) && (
                              <span className="px-2 py-0.5 bg-gray-800 rounded">Tool: {ev.payload?.tool ?? ev.metadata?.tool ?? ev.metadata?.params?.tool}</span>
                            )}
                            {ev.event_type === 'tool_result' && (ev.payload?.tool || ev.metadata?.tool || ev.metadata?.params?.tool) && (
                              <span className="px-2 py-0.5 bg-gray-800 rounded">{ev.payload?.tool ?? ev.metadata?.tool ?? ev.metadata?.params?.tool}{ev.payload?.status ? ` - ${ev.payload.status}` : ''}</span>
                            )}
                            {ev.event_type === 'delegation' && (ev.payload?.target_agent || ev.metadata?.target_agent || ev.input?.target_agent) && (
                              <span className="px-2 py-0.5 bg-gray-800 rounded">→ {ev.payload?.target_agent ?? ev.metadata?.target_agent ?? ev.input?.target_agent}</span>
                            )}
                            {ev.event_type === 'llm_usage' && (
                              <>
                                <span className="px-2 py-0.5 bg-cyan-400/10 text-cyan-300 rounded font-medium">{ev.metadata.model || 'model'}</span>
                                <span className="text-gray-400">{fmtNumber(ev.metadata?.prompt_tokens ?? 0)} in</span>
                                <span className="text-gray-400">/ {fmtNumber(ev.metadata?.completion_tokens ?? 0)} out</span>
                              </>
                            )}
                          </div>
                        </div>
          </div>

          {/* Inline expanded details (payload / metadata / input / output) - hidden when collapsed */}
          {isExpanded && (
            <div
              className="bg-[#0D0E0E] px-4 py-3 border-t border-gray-800"
              style={{ paddingLeft: `${depth * 24 + 16}px` }}
            >
              <div className="space-y-3 text-sm">
                {/* For llm_usage - show provider, model, token details */}
                {ev.event_type === "llm_usage" && ev.metadata && (
                  <div>
                    <div className="text-xs font-semibold text-gray-400 mb-1">
                      LLM Usage
                    </div>
                    <div className="bg-[#191A1A] rounded p-2 text-xs border border-gray-800 space-y-1">
                      {ev.metadata.provider && (
                        <div>
                          <span className="text-gray-500">Provider:</span>
                          <span className="ml-2 text-gray-300">{ev.metadata.provider}</span>
                        </div>
                      )}
                      {ev.metadata.model && (
                        <div>
                          <span className="text-gray-500">Model:</span>
                          <span className="ml-2 text-gray-300">{ev.metadata.model}</span>
                        </div>
                      )}
                      {ev.metadata.prompt_tokens !== undefined && (
                        <div>
                          <span className="text-gray-500">Prompt Tokens:</span>
                          <span className="ml-2 text-gray-300">{fmtNumber(ev.metadata.prompt_tokens)}</span>
                        </div>
                      )}
                      {ev.metadata.completion_tokens !== undefined && (
                        <div>
                          <span className="text-gray-500">Completion Tokens:</span>
                          <span className="ml-2 text-gray-300">{fmtNumber(ev.metadata.completion_tokens)}</span>
                        </div>
                      )}
                      {ev.metadata.total_tokens !== undefined && (
                        <div>
                          <span className="text-gray-500">Total Tokens:</span>
                          <span className="ml-2 text-cyan-400 font-semibold">{fmtNumber(ev.metadata.total_tokens)}</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* For autonomous_think - show response and timing */}
                {ev.event_type === "autonomous_think" && ev.metadata && (
                  <>
                    {ev.metadata.response && (
                      <div>
                        <div className="flex items-center justify-between mb-1">
                          <div className="text-xs font-semibold text-gray-400">
                            Reasoning Response
                            <span className="ml-2 text-gray-500 font-normal">(
                              {typeof ev.metadata.response === "string"
                                ? fmtNumber(ev.metadata.response.length)
                                : fmtNumber(JSON.stringify(ev.metadata.response).length)} chars)
                            </span>
                          </div>
                          <button
                            onClick={() => {
                              const text = typeof ev.metadata.response === "string"
                                ? ev.metadata.response
                                : JSON.stringify(ev.metadata.response, null, 2);
                              navigator.clipboard.writeText(text);
                            }}
                            className="text-xs px-2 py-1 bg-[#1FB8CD]/10 hover:bg-[#1FB8CD]/20 text-[#1FB8CD] rounded border border-[#1FB8CD]/30 transition-colors"
                          >
                            Copy
                          </button>
                        </div>
                        <div className="bg-[#191A1A] rounded p-3 border border-gray-800 max-h-96 overflow-y-auto">
                          <pre className="text-xs text-gray-300 whitespace-pre-wrap break-words">
                            {typeof ev.metadata.response === "string"
                              ? ev.metadata.response
                              : JSON.stringify(ev.metadata.response, null, 2)}
                          </pre>
                        </div>
                      </div>
                    )}
                    {ev.metadata.iteration !== undefined && (
                      <div className="bg-[#191A1A] rounded p-2 text-xs border border-gray-800 mt-2">
                        <span className="text-gray-500">Iteration:</span>
                        <span className="ml-2 text-gray-300">{ev.metadata.iteration}</span>
                        {ev.metadata.duration_ms && (
                          <>
                            <span className="text-gray-500 ml-4">Duration:</span>
                            <span className="ml-2 text-gray-300">{(ev.metadata.duration_ms / 1000).toFixed(2)}s</span>
                          </>
                        )}
                      </div>
                    )}
                  </>
                )}

                {/* Standard Input (for other event types) */}
                {ev.event_type !== "llm_usage" && ev.event_type !== "autonomous_think" && ev.input && Object.keys(ev.input).length > 0 && (
                  <div>
                    <div className="text-xs font-semibold text-gray-400 mb-1">Input</div>
                    <pre className="bg-[#191A1A] rounded p-2 text-xs text-gray-300 overflow-x-auto border border-gray-800">{JSON.stringify(ev.input, null, 2)}</pre>
                  </div>
                )}

                {/* Standard Output (for other event types) */}
                {ev.event_type !== "llm_usage" && ev.event_type !== "autonomous_think" && (ev.output || ev.metadata.error) && (
                  <div>
                    <div className="text-xs font-semibold text-gray-400 mb-1">Output</div>
                    <pre className="bg-[#191A1A] rounded p-2 text-xs text-gray-300 overflow-x-auto border border-gray-800">{JSON.stringify(ev.output || ev.metadata.error, null, 2)}</pre>
                  </div>
                )}

                {/* Metadata */}
                <div>
                  <div className="text-xs font-semibold text-gray-400 mb-1">Metadata</div>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <span className="text-gray-500">Agent:</span>
                      <span className="ml-2 text-gray-300">{ev.agent || ev.agent_name || '-'}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Event:</span>
                      <span className="ml-2 text-gray-300">{ev.event_type}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Time:</span>
                      <span className="ml-2 text-gray-300">{ev.start_time ? new Date(ev.start_time).toLocaleTimeString() : (ev.timestamp ? new Date(ev.timestamp).toLocaleTimeString() : '')}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Always render children (trace structure) regardless of details collapsed/expanded */}
        {hasChildren && (
          <div>
            {node.children.map((c, i) => (
              <TraceNodeRow
                key={c.event?.id ?? `${depth}-${i}`}
                node={c}
                depth={depth + 1}
              />
            ))}
          </div>
        )}
      </div>
    );
  }

  const traceTree = buildTraceTree(spans || []);

  return (
    <div className="h-[calc(100vh-56px)] flex flex-col bg-[#191A1A]">
      {/* Header */}
      <div className="flex-none px-6 py-4 border-b border-gray-800">
        <h1 className="text-2xl font-bold text-white">Playground</h1>
        <p className="text-sm text-gray-400 mt-1">
          Test your agents with custom prompts
        </p>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Left Side - Prompt Input */}
        <div className="flex-1 flex flex-col border-r border-gray-800">
          <div className="flex-none px-6 py-4 border-b border-gray-800">
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Prompt / Query
            </label>
          </div>

          <div className="flex-1 p-6">
            <textarea
              value={promptText}
              onChange={(e) => setPromptText(e.target.value)}
              className="w-full h-full bg-[#1F2121] border border-gray-800 rounded-lg px-4 py-3 text-white text-sm resize-none focus:outline-none focus:border-[#1FB8CD] transition-colors"
              placeholder="Enter your prompt here...

Example: Research the top 5 programming languages in 2024 and write a comparison report."
            />
          </div>

          <div className="flex-none px-6 py-4 border-t border-gray-800 flex items-center justify-between">
            <div className="text-sm text-gray-400">
              {promptText.length} characters
            </div>
            <div className="flex items-center gap-3">
              {runPlayground.isPending && (
                <button
                  onClick={handleCancel}
                  disabled={cancelPlayground.isPending}
                  className="flex items-center gap-2 px-4 py-2.5 bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30 rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <StopCircle className="w-4 h-4" />
                  {cancelPlayground.isPending ? "Canceling..." : "Cancel"}
                </button>
              )}
              <button
                onClick={handleRun}
                disabled={
                  runPlayground.isPending ||
                  !promptText.trim() ||
                  (mode === "sequential" && selectedAgents.length < 2)
                }
                className="flex items-center gap-2 px-6 py-2.5 bg-[#1FB8CD] hover:bg-[#1AA5B8] text-white rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <Play className="w-4 h-4" />
                {runPlayground.isPending ? "Running..." : "Run"}
              </button>
            </div>
          </div>
        </div>

        {/* Right Side - Configuration */}
        <div className="w-96 flex flex-col bg-[#1A1B1B]">
          {/* Mode Selection */}
          <div className="flex-none px-6 py-4 border-b border-gray-800">
            <label className="block text-sm font-medium text-gray-300 mb-3">
              Mode
            </label>
            <div className="space-y-2">
              <label className="flex items-center gap-3 p-3 bg-[#1F2121] border border-gray-800 rounded-lg cursor-pointer hover:border-[#1FB8CD] transition-colors">
                <input
                  type="radio"
                  name="mode"
                  checked={mode === "single"}
                  onChange={() => setMode("single")}
                  className="w-4 h-4 text-[#1FB8CD] focus:ring-[#1FB8CD] focus:ring-offset-0"
                />
                <div className="flex-1">
                  <div className="text-white font-medium">Single Agent</div>
                  <div className="text-xs text-gray-400">
                    Run with one agent
                  </div>
                </div>
              </label>
              <label className="flex items-center gap-3 p-3 bg-[#1F2121] border border-gray-800 rounded-lg cursor-pointer hover:border-[#1FB8CD] transition-colors">
                <input
                  type="radio"
                  name="mode"
                  checked={mode === "sequential"}
                  onChange={() => setMode("sequential")}
                  className="w-4 h-4 text-[#1FB8CD] focus:ring-[#1FB8CD] focus:ring-offset-0"
                />
                <div className="flex-1">
                  <div className="text-white font-medium">Sequential Run</div>
                  <div className="text-xs text-gray-400">
                    Chain multiple agents
                  </div>
                </div>
              </label>
            </div>
          </div>

          {/* Agent Selection */}
          <div className="flex-1 overflow-y-auto px-6 py-4">
            <label className="block text-sm font-medium text-gray-300 mb-3">
              {mode === "single" ? "Select Agent" : "Select Agents (in order)"}
            </label>

            {mode === "single" ? (
              <div className="space-y-2">
                {agents &&
                  agents.map((agent) => (
                    <label
                      key={agent.name}
                      className={`flex items-center gap-3 p-3 border rounded-lg cursor-pointer transition-colors ${
                        selectedAgent === agent.name
                          ? "bg-[#1FB8CD]/10 border-[#1FB8CD]"
                          : "bg-[#1F2121] border-gray-800 hover:border-gray-700"
                      }`}
                    >
                      <input
                        type="radio"
                        name="agent"
                        checked={selectedAgent === agent.name}
                        onChange={() => setSelectedAgent(agent.name)}
                        className="w-4 h-4 text-[#1FB8CD] focus:ring-[#1FB8CD] focus:ring-offset-0"
                      />
                      <div className="flex-1 min-w-0">
                        <div className="text-white font-medium">
                          {agent.name}
                        </div>
                        <div className="text-xs text-gray-400 truncate">
                          {agent.role}
                        </div>
                      </div>
                    </label>
                  ))}
              </div>
            ) : (
              <div className="space-y-2">
                {agents &&
                  agents.map((agent) => {
                    const isSelected = selectedAgents.includes(agent.name);
                    const order = isSelected
                      ? selectedAgents.indexOf(agent.name) + 1
                      : null;

                    return (
                      <label
                        key={agent.name}
                        className={`flex items-center gap-3 p-3 border rounded-lg cursor-pointer transition-colors ${
                          isSelected
                            ? "bg-[#1FB8CD]/10 border-[#1FB8CD]"
                            : "bg-[#1F2121] border-gray-800 hover:border-gray-700"
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => toggleAgentSelection(agent.name)}
                          className="w-4 h-4 text-[#1FB8CD] rounded focus:ring-[#1FB8CD] focus:ring-offset-0"
                        />
                        <div className="flex-1 min-w-0">
                          <div className="text-white font-medium">
                            {agent.name}
                          </div>
                          <div className="text-xs text-gray-400 truncate">
                            {agent.role}
                          </div>
                        </div>
                        {order && (
                          <div className="flex items-center justify-center w-6 h-6 rounded-full bg-[#1FB8CD] text-white text-xs font-bold">
                            {order}
                          </div>
                        )}
                      </label>
                    );
                  })}
                {selectedAgents.length > 0 && (
                  <div className="mt-3 p-3 bg-[#1F2121] border border-gray-800 rounded-lg">
                    <div className="text-xs text-gray-400 mb-1">
                      Execution order:
                    </div>
                    <div className="text-sm text-white">
                      {selectedAgents.join(" → ")}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Live Trace Section */}
      {/* Live Trace Panel - Bottom */}
      {showTraces && activePlaygroundId && (
        <div className="flex-none border-t-2 border-t-[#1FB8CD] bg-[#0D0E0E] shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.3)] transition-all duration-300 ease-in-out">
          <div className="px-6 py-3 border-b border-gray-800 flex items-center justify-between bg-[#0D0E0E]">
            <div className="flex items-center gap-3">
              <h2 className="text-sm font-semibold text-white">Live Trace</h2>
              {isConnected && !isComplete && (
                <span className="flex items-center gap-1.5 text-xs text-cyan-400">
                  <span className="w-2 h-2 bg-cyan-400 rounded-full animate-pulse" />
                  Running
                </span>
              )}
              {isComplete && (
                <span className="text-xs px-2 py-1 rounded bg-green-500/20 text-green-400">
                  Completed
                </span>
              )}
            </div>

            <div className="flex items-center gap-4">
              {/* Cancel button - only show when running */}
              {!isComplete && (
                <button
                  onClick={handleCancel}
                  disabled={cancelPlayground.isPending}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30 rounded font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <StopCircle className="w-3.5 h-3.5" />
                  {cancelPlayground.isPending ? "Canceling..." : "Cancel"}
                </button>
              )}

              {/* Summary Metrics */}
              {spans.length > 0 && (
                <div className="flex items-center gap-6 text-xs text-gray-400">
                  <div className="flex items-center gap-1.5">
                    <Database className="w-3.5 h-3.5" />
                    <span>{spans.length} spans</span>
                  </div>
                  {totalTokens > 0 && (
                    <div className="flex items-center gap-1.5">
                      <Zap className="w-3.5 h-3.5" />
                      <span>{totalTokens.toLocaleString()} tokens</span>
                    </div>
                  )}
                  {/* Only show duration when complete */}
                  {isComplete && totalDuration > 0 && (
                    <div className="flex items-center gap-1.5">
                      <Clock className="w-3.5 h-3.5" />
                      <span>{(totalDuration / 1000).toFixed(2)}s</span>
                    </div>
                  )}
                </div>
              )}

              {/* Close Button */}
              <button
                onClick={handleCloseTraces}
                className="p-1.5 hover:bg-[#2A2C2C] rounded text-gray-400 hover:text-white transition-colors"
                aria-label="Close trace panel"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          <div className="h-96 overflow-y-auto bg-[#191A1A]">
            {spans.length === 0 ? (
              <div className="flex items-center justify-center h-full text-gray-500">
                <div className="text-center">
                  <Activity className="w-12 h-12 mx-auto mb-3 opacity-50" />
                  <p className="text-sm">Waiting for traces...</p>
                </div>
              </div>
            ) : (
              <div className="p-4 space-y-1">
                {traceTree.map((node, index) => (
                  <div
                    key={`trace-${index}-${node.event.id ?? index}`}
                    className="opacity-0 animate-[fadeInSlide_0.3s_ease-out_forwards]"
                    style={{ animationDelay: `${index * 50}ms` }}
                  >
                    <TraceNodeRow node={node} depth={0} />
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

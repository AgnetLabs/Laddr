import { useParams, Link } from 'react-router-dom';
import { usePrompt } from '../lib/queries/prompts';
import { usePlaygroundTraces } from '../lib/hooks/useWebSocket';
import { useCancelPlayground } from '../lib/queries/playground';
import { ArrowLeft, CheckCircle, XCircle, Loader2, Clock, Activity, Database, Code, Brain, ChevronDown, ChevronRight, Zap, StopCircle } from 'lucide-react';
import { format } from 'date-fns';
import { useState } from 'react';

interface Span {
  id: number;
  name: string;
  type: 'agent' | 'tool' | 'llm' | 'reasoning' | 'event';
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

interface SpanTreeNodeProps {
  span: Span;
  depth: number;
}

function SpanTreeNode({ span, depth }: SpanTreeNodeProps) {
  const [isExpanded, setIsExpanded] = useState(true);
  const hasChildren = span.children && span.children.length > 0;

  return (
    <>
      <SpanRow
        span={span}
        depth={depth}
        isExpanded={isExpanded}
        onToggle={() => setIsExpanded(!isExpanded)}
      />
      {hasChildren && isExpanded && (
        <>
          {span.children.map((child) => (
            <SpanTreeNode key={child.id} span={child} depth={depth + 1} />
          ))}
        </>
      )}
    </>
  );
}

interface SpanRowProps {
  span: Span;
  depth: number;
  isExpanded: boolean;
  onToggle: () => void;
}

function SpanRow({ span, depth, isExpanded, onToggle }: SpanRowProps) {
  const hasChildren = span.children && span.children.length > 0;
  
  const getIcon = () => {
    switch (span.type) {
      case 'agent':
        return <Activity className="w-4 h-4 text-cyan-400" />;
      case 'tool':
        return <Code className="w-4 h-4 text-purple-400" />;
      case 'llm':
        return <Brain className="w-4 h-4 text-green-400" />;
      case 'reasoning':
        return <Database className="w-4 h-4 text-yellow-400" />;
      default:
        return <div className="w-4 h-4 rounded-full bg-gray-600" />;
    }
  };

  const formatDuration = (ms?: number) => {
    if (!ms) return null;
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  return (
    <div className="border-b border-gray-800">
      <div
        className="flex items-center gap-3 py-3 px-4 hover:bg-[#1F2121] cursor-pointer transition-colors"
        style={{ paddingLeft: `${depth * 24 + 16}px` }}
        onClick={onToggle}
      >
        <div className="w-4 h-4 flex-shrink-0">
          {hasChildren && (
            isExpanded ? (
              <ChevronDown className="w-4 h-4 text-gray-400" />
            ) : (
              <ChevronRight className="w-4 h-4 text-gray-400" />
            )
          )}
        </div>

        {getIcon()}

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-white truncate">
              {span.name || span.event_type}
            </span>
            <span className="text-xs text-gray-500">
              {span.type}
            </span>
          </div>
          {span.agent && (
            <div className="text-xs text-gray-400 mt-0.5">
              {span.agent}
            </div>
          )}
        </div>

        <div className="flex items-center gap-4 text-xs text-gray-400">
          {typeof span.metadata?.tokens === 'number' && (
            <div className="flex items-center gap-1">
              <Zap className="w-3.5 h-3.5" />
              <span>{span.metadata.tokens.toLocaleString()}</span>
            </div>
          )}
          {span.metadata?.duration_ms && (
            <div className="flex items-center gap-1">
              <Clock className="w-3.5 h-3.5" />
              <span>{formatDuration(span.metadata.duration_ms)}</span>
            </div>
          )}
        </div>
      </div>

      {isExpanded && (span.input || span.output || span.event_type === 'llm_usage' || span.event_type === 'autonomous_think') && (
        <div className="px-4 pb-3 bg-[#0D0E0E]" style={{ paddingLeft: `${depth * 24 + 72}px` }}>
          {/* For llm_usage - show provider, model, token details */}
          {span.event_type === 'llm_usage' && span.metadata && (
            <div className="mb-2">
              <div className="text-xs text-gray-500 mb-1">LLM Usage:</div>
              <div className="text-xs text-gray-300 bg-[#191A1A] p-2 rounded space-y-1">
                {span.metadata.provider && (
                  <div>
                    <span className="text-gray-500">Provider:</span>
                    <span className="ml-2 text-gray-300">{span.metadata.provider}</span>
                  </div>
                )}
                {span.metadata.model && (
                  <div>
                    <span className="text-gray-500">Model:</span>
                    <span className="ml-2 text-gray-300">{span.metadata.model}</span>
                  </div>
                )}
                {span.metadata.prompt_tokens != null && (
                  <div>
                    <span className="text-gray-500">Prompt Tokens:</span>
                    <span className="ml-2 text-gray-300">{Number(span.metadata.prompt_tokens).toLocaleString()}</span>
                  </div>
                )}
                {span.metadata.completion_tokens != null && (
                  <div>
                    <span className="text-gray-500">Completion Tokens:</span>
                    <span className="ml-2 text-gray-300">{Number(span.metadata.completion_tokens).toLocaleString()}</span>
                  </div>
                )}
                {span.metadata.total_tokens != null && (
                  <div>
                    <span className="text-gray-500">Total Tokens:</span>
                    <span className="ml-2 text-cyan-400 font-semibold">{Number(span.metadata.total_tokens).toLocaleString()}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* For autonomous_think - show response and timing */}
          {span.event_type === 'autonomous_think' && span.metadata && (
            <>
              {span.metadata.response && (
                <div className="mb-2">
                  <div className="flex items-center justify-between mb-1">
                    <div className="text-xs text-gray-500">
                      Reasoning Response:
                      <span className="ml-2 text-gray-400">
                        ({typeof span.metadata.response === 'string' 
                          ? span.metadata.response.length.toLocaleString() 
                          : JSON.stringify(span.metadata.response).length.toLocaleString()} chars)
                      </span>
                    </div>
                    <button
                      onClick={() => {
                        const text = typeof span.metadata.response === 'string' 
                          ? span.metadata.response 
                          : JSON.stringify(span.metadata.response, null, 2);
                        navigator.clipboard.writeText(text);
                      }}
                      className="text-xs px-2 py-1 bg-[#1FB8CD]/10 hover:bg-[#1FB8CD]/20 text-[#1FB8CD] rounded border border-[#1FB8CD]/30 transition-colors"
                    >
                      Copy
                    </button>
                  </div>
                  <div className="text-xs text-gray-300 bg-[#191A1A] p-3 rounded border border-gray-800 max-h-96 overflow-y-auto">
                    <pre className="whitespace-pre-wrap break-words">
                      {typeof span.metadata.response === 'string' 
                        ? span.metadata.response 
                        : JSON.stringify(span.metadata.response, null, 2)}
                    </pre>
                  </div>
                </div>
              )}
              {span.metadata.iteration !== undefined && (
                <div className="mb-2">
                  <div className="text-xs text-gray-500 mb-1">Details:</div>
                  <div className="text-xs text-gray-300 bg-[#191A1A] p-2 rounded border border-gray-800">
                    <span className="text-gray-500">Iteration:</span>
                    <span className="ml-2 text-gray-300">{span.metadata.iteration}</span>
                    {span.metadata.duration_ms && (
                      <>
                        <span className="text-gray-500 ml-4">Duration:</span>
                        <span className="ml-2 text-gray-300">{(span.metadata.duration_ms / 1000).toFixed(2)}s</span>
                      </>
                    )}
                  </div>
                </div>
              )}
            </>
          )}

          {/* Standard Input (for other event types) */}
          {span.event_type !== 'llm_usage' && span.event_type !== 'autonomous_think' && span.input && (
            <div className="mb-2">
              <div className="text-xs text-gray-500 mb-1">Input:</div>
              <pre className="text-xs text-gray-300 bg-[#191A1A] p-2 rounded overflow-x-auto">
                {typeof span.input === 'string' ? span.input : JSON.stringify(span.input, null, 2)}
              </pre>
            </div>
          )}

          {/* Standard Output (for other event types) */}
          {span.event_type !== 'llm_usage' && span.event_type !== 'autonomous_think' && span.output && (
            <div>
              <div className="text-xs text-gray-500 mb-1">Output:</div>
              <pre className="text-xs text-gray-300 bg-[#191A1A] p-2 rounded overflow-x-auto">
                {typeof span.output === 'string' ? span.output : JSON.stringify(span.output, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function PlaygroundDetail() {
  const { promptId } = useParams<{ promptId: string }>();
  const { data: prompt, isLoading } = usePrompt(promptId!);
  const { traces, isConnected, isComplete } = usePlaygroundTraces(promptId || null);
  const cancelPlayground = useCancelPlayground();

  const getStatusIcon = () => {
    switch (prompt?.status) {
      case 'completed':
        return <CheckCircle className="w-8 h-8 text-green-500" />;
      case 'error':
      case 'failed':
        return <XCircle className="w-8 h-8 text-red-500" />;
      case 'running':
        return <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />;
      case 'canceled':
        return <XCircle className="w-8 h-8 text-gray-500" />;
      default:
        return <Clock className="w-8 h-8 text-gray-400" />;
    }
  };

  const handleCancel = async () => {
    if (!promptId) return;
    try {
      await cancelPlayground.mutateAsync(promptId);
    } catch (error) {
      console.error('Failed to cancel:', error);
    }
  };

  // Extract spans from traces
  const spans: Span[] = traces.length > 0 && traces[0].spans ? traces[0].spans : [];

  // Calculate metrics
  const calculateTotalTokens = (spanList: Span[]): number => {
    return spanList.reduce((sum, span) => {
      const spanTokens = span.metadata?.tokens || 0;
      const childTokens = calculateTotalTokens(span.children || []);
      return sum + spanTokens + childTokens;
    }, 0);
  };

  const calculateTotalDuration = (spanList: Span[]): number => {
    if (spanList.length === 0) return 0;
    try {
      const firstSpan = spanList[0];
      const firstStartTime = new Date(firstSpan.start_time).getTime();
      const lastSpan = spanList[spanList.length - 1];
      const lastStartTime = new Date(lastSpan.start_time).getTime();
      return lastStartTime - firstStartTime;
    } catch (e) {
      return 0;
    }
  };

  const totalTokens = calculateTotalTokens(spans);
  const totalDuration = calculateTotalDuration(spans);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-gray-400">Loading playground run...</p>
      </div>
    );
  }

  if (!prompt) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-400">Playground run not found</p>
        <Link to="/playground-history" className="text-[#1FB8CD] hover:text-[#1AA5B8] mt-4 inline-block">
          Back to history
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#191A1A] p-6 space-y-6">
      <div className="flex items-center gap-4">
        <Link to="/playground-history" className="p-2 hover:bg-[#1F2121] rounded-lg transition-colors">
          <ArrowLeft className="w-5 h-5 text-gray-400" />
        </Link>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-white">Playground Run Details</h1>
          <code className="text-gray-400 text-sm">{prompt.prompt_id}</code>
        </div>
        {prompt.status === 'running' && (
          <button
            onClick={handleCancel}
            disabled={cancelPlayground.isPending}
            className="flex items-center gap-2 px-4 py-2 bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30 rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <StopCircle className="w-4 h-4" />
            {cancelPlayground.isPending ? 'Canceling...' : 'Cancel Run'}
          </button>
        )}
      </div>

      <div className="bg-[#1F2121] rounded-lg p-6 border border-gray-800">
        <div className="flex items-center gap-4 mb-6">
          {getStatusIcon()}
          <div>
            <h2 className="text-2xl font-bold text-white capitalize">{prompt.status}</h2>
            <p className="text-gray-400">Agent: {prompt.prompt_name}</p>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <h3 className="text-sm font-medium text-gray-400 mb-1">Created</h3>
            <p className="text-white">{prompt.created_at ? format(new Date(prompt.created_at), 'MMM d, yyyy HH:mm:ss') : '-'}</p>
          </div>
          {prompt.completed_at && (
            <div>
              <h3 className="text-sm font-medium text-gray-400 mb-1">Completed</h3>
              <p className="text-white">{format(new Date(prompt.completed_at), 'MMM d, yyyy HH:mm:ss')}</p>
            </div>
          )}
          {prompt.token_usage?.total_tokens !== undefined && (
            <div className="col-span-2 md:col-span-2">
              <h3 className="text-sm font-medium text-gray-400 mb-1">Token usage</h3>
              <div className="flex items-center gap-3 text-white">
                <Database className="w-4 h-4 text-[#1FB8CD]" />
                <span className="text-sm">
                  total: <span className="font-semibold">{prompt.token_usage.total_tokens}</span>
                </span>
                <span className="text-xs text-gray-400">
                  (prompt: {prompt.token_usage.prompt_tokens ?? 0}, completion: {prompt.token_usage.completion_tokens ?? 0})
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Live Traces Section */}
      {(prompt.status === 'running' || spans.length > 0) && (
        <div className="border-t-2 border-t-[#1FB8CD] bg-[#0D0E0E] rounded-lg shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.3)]">
          <div className="px-6 py-3 border-b border-gray-800 bg-[#0D0E0E] flex items-center justify-between">
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
            
            <div className="flex items-center gap-6">
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
                  {isComplete && totalDuration > 0 && (
                    <div className="flex items-center gap-1.5">
                      <Clock className="w-3.5 h-3.5" />
                      <span>{(totalDuration / 1000).toFixed(2)}s</span>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          <div className="h-96 overflow-y-auto bg-[#0D0E0E]">
            {spans.length === 0 ? (
              <div className="flex items-center justify-center h-full text-gray-500">
                <div className="text-center">
                  <Activity className="w-12 h-12 mx-auto mb-3 opacity-50" />
                  <p className="text-sm">Waiting for traces...</p>
                </div>
              </div>
            ) : (
              <div className="p-4 space-y-1">
                {spans.map((span, index) => (
                  <div 
                    key={`${span.id}-${index}`}
                    className="opacity-0 animate-[fadeInSlide_0.3s_ease-out_forwards]"
                    style={{ animationDelay: `${index * 50}ms` }}
                  >
                    <SpanTreeNode span={span} depth={0} />
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {prompt.outputs && (
        <div className="bg-[#1F2121] rounded-lg border border-gray-800">
          <div className="px-6 py-4 border-b border-gray-800">
            <h2 className="text-lg font-semibold text-white">Outputs</h2>
          </div>
          <div className="p-6">
            <div className="bg-[#0D0E0E] rounded-lg p-4 border border-gray-800">
              <pre className="text-sm text-gray-300 overflow-x-auto whitespace-pre-wrap">
                {typeof prompt.outputs === 'string' 
                  ? prompt.outputs 
                  : JSON.stringify(prompt.outputs, null, 2)}
              </pre>
            </div>
          </div>
        </div>
      )}

      {prompt.error && (
        <div className="bg-[#1F2121] rounded-lg border border-red-700">
          <div className="px-6 py-4 border-b border-red-700">
            <h2 className="text-lg font-semibold text-red-500">Error</h2>
          </div>
          <div className="p-6">
            <pre className="bg-[#0D0E0E] rounded-lg p-4 text-sm text-red-400 overflow-x-auto">
              {prompt.error}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}

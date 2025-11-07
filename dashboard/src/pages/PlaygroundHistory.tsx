import { usePlaygrounds } from '../lib/queries/playground';
import { Clock, CheckCircle, XCircle, Loader2, Play, ChevronDown, ChevronRight } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { format } from 'date-fns';
import { useState } from 'react';
import { usePlaygroundTraces } from '../lib/hooks/useWebSocket';

export default function PlaygroundHistory() {
  const { data: playgrounds, isLoading } = usePlaygrounds(50);
  const navigate = useNavigate();
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());

  const toggleRow = (id: string) => {
    const next = new Set(expandedRows);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setExpandedRows(next);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-400" />;
      case 'error':
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-400" />;
      case 'running':
        return <Loader2 className="w-5 h-5 text-blue-400 animate-spin" />;
      case 'canceled':
        return <XCircle className="w-5 h-5 text-gray-400" />;
      default:
        return <Clock className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-400 bg-green-400/10';
      case 'error':
      case 'failed':
        return 'text-red-400 bg-red-400/10';
      case 'running':
        return 'text-blue-400 bg-blue-400/10';
      case 'canceled':
        return 'text-gray-400 bg-gray-400/10';
      default:
        return 'text-gray-400 bg-gray-400/10';
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-gray-400">Loading playground history...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 bg-[#191A1A] p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Playground History</h1>
          <p className="text-sm text-gray-400 mt-1">View past playground executions</p>
        </div>
        <Link
          to="/playground"
          className="flex items-center gap-2 px-4 py-2 bg-[#1FB8CD] hover:bg-[#1AA5B8] text-white rounded-lg transition-colors"
        >
          <Play className="w-4 h-4" />
          New Run
        </Link>
      </div>

      <div className="bg-[#1F2121] rounded-lg border border-gray-800 overflow-hidden">
        {!playgrounds || playgrounds.length === 0 ? (
          <div className="text-center py-12 text-gray-400">
            <Clock className="w-12 h-12 mx-auto mb-4 text-gray-600" />
            <p>No playground runs found</p>
            <Link
              to="/playground"
              className="inline-flex items-center gap-2 mt-4 text-[#1FB8CD] hover:text-[#1AA5B8]"
            >
              <Play className="w-4 h-4" />
              Start your first run
            </Link>
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-[#191A1A]">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Agent/Mode
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Tokens
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Created
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Duration
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {playgrounds.map((playground) => {
                const duration = playground.completed_at && playground.created_at
                  ? Math.round(
                      (new Date(playground.completed_at).getTime() -
                        new Date(playground.created_at).getTime()) /
                        1000
                    )
                  : null;
                const isExpanded = expandedRows.has(playground.prompt_id);

                return (
                  <>
                    <tr
                      key={playground.prompt_id}
                      className="hover:bg-[#252525] transition-colors cursor-pointer"
                    >
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <button
                            onClick={(e) => { e.stopPropagation(); toggleRow(playground.prompt_id); }}
                            className="p-1 rounded hover:bg-gray-800/20"
                            aria-label={isExpanded ? 'Collapse' : 'Expand'}
                          >
                            {isExpanded ? <ChevronDown className="w-4 h-4 text-gray-300" /> : <ChevronRight className="w-4 h-4 text-gray-500" />}
                          </button>
                          {getStatusIcon(playground.status)}
                          <span className={`text-xs px-2 py-1 rounded font-medium ${getStatusColor(playground.status)}`}>
                            {playground.status}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4" onClick={() => navigate(`/playground-history/${playground.prompt_id}`)}>
                        <code className="text-sm text-gray-300 font-mono">{playground.prompt_id.slice(0, 8)}</code>
                      </td>
                      <td className="px-6 py-4" onClick={() => navigate(`/playground-history/${playground.prompt_id}`)}>
                        <div className="text-white font-medium">{playground.prompt_name}</div>
                      </td>
                      <td className="px-6 py-4" onClick={() => navigate(`/playground-history/${playground.prompt_id}`)}>
                        {playground.token_usage?.total_tokens ? (
                          <span className="text-gray-300">{playground.token_usage.total_tokens.toLocaleString()}</span>
                        ) : (
                          <span className="text-gray-500">-</span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-gray-400" onClick={() => navigate(`/playground-history/${playground.prompt_id}`)}>
                        {playground.created_at ? format(new Date(playground.created_at), 'MMM d, HH:mm:ss') : '-'}
                      </td>
                      <td className="px-6 py-4 text-gray-400" onClick={() => navigate(`/playground-history/${playground.prompt_id}`)}>
                        {duration !== null ? `${duration}s` : '-'}
                      </td>
                    </tr>

                    {isExpanded && (
                      <tr key={`${playground.prompt_id}-details`} className="bg-[#121212]">
                        <td colSpan={6} className="px-6 py-4">
                          <ExpandedDetails playground={playground} />
                        </td>
                      </tr>
                    )}
                  </>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

function ExpandedDetails({ playground }: { playground: any }) {
  // fetch traces for this playground run (live or historical)
  const { traces } = usePlaygroundTraces(playground.prompt_id || null);

  // traces shape: [{ spans: Span[] }] in PlaygroundDetail; fall back to empty
  const spans = traces && traces.length > 0 && traces[0].spans ? traces[0].spans : [];

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <div className="text-xs text-gray-400">Inputs</div>
          <div className="bg-[#0D0E0E] rounded p-3 mt-2 text-xs text-gray-300 max-h-48 overflow-auto">
            <pre className="whitespace-pre-wrap">{JSON.stringify(playground.inputs || {}, null, 2)}</pre>
          </div>
        </div>

        <div>
          <div className="text-xs text-gray-400">Outputs</div>
          <div className="bg-[#0D0E0E] rounded p-3 mt-2 text-xs text-gray-300 max-h-48 overflow-auto">
            <pre className="whitespace-pre-wrap">{typeof playground.outputs === 'string' ? playground.outputs : JSON.stringify(playground.outputs || {}, null, 2)}</pre>
          </div>
        </div>
      </div>

      <div>
        <div className="text-xs text-gray-400">Token Usage</div>
        <div className="mt-2 text-xs text-gray-300 bg-[#0D0E0E] p-3 rounded">
          <div>Total: <span className="font-semibold">{playground.token_usage?.total_tokens ?? 0}</span></div>
          <div>Prompt: {playground.token_usage?.prompt_tokens ?? 0}</div>
          <div>Completion: {playground.token_usage?.completion_tokens ?? 0}</div>
        </div>
      </div>

      <div>
        <div className="text-xs text-gray-400 mb-2">Traces</div>
        {spans.length === 0 ? (
          <div className="text-xs text-gray-500">No trace spans available for this run.</div>
        ) : (
          <div className="bg-[#0D0E0E] rounded p-2 space-y-2 max-h-72 overflow-auto">
            {spans.map((s: any, i: number) => (
              <SpanNode key={`${s.id}-${i}`} span={s} depth={0} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function SpanNode({ span, depth }: { span: any; depth: number }) {
  const [open, setOpen] = useState(true);
  const hasChildren = span.children && span.children.length > 0;

  return (
    <div>
      <div
        className="flex items-center gap-3 py-2 px-3 hover:bg-gray-900/10 rounded cursor-pointer"
        style={{ paddingLeft: `${depth * 16}px` }}
        onClick={() => setOpen(!open)}
      >
        <div className="w-4">
          {hasChildren ? (open ? <ChevronDown className="w-4 h-4 text-gray-300" /> : <ChevronRight className="w-4 h-4 text-gray-500" />) : <div className="w-4" />}
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-sm text-white truncate">{span.name || span.event_type}</div>
          <div className="text-xs text-gray-400">{span.agent || ''} — {span.event_type}</div>
        </div>
        <div className="text-xs text-gray-400">
          {span.metadata?.tokens ? `${span.metadata.tokens} tokens` : ''}
        </div>
      </div>

      {open && (
        <div className="ml-8 mt-2 mb-2 text-xs text-gray-300 bg-[#121212] p-3 rounded">
          {/* Metadata */}
          {span.metadata && (
            <div className="mb-2">
              <div className="text-xs text-gray-400">Metadata</div>
              <pre className="whitespace-pre-wrap text-xs mt-1">{JSON.stringify(span.metadata, null, 2)}</pre>
            </div>
          )}

          {/* Input / Output */}
          {span.input && (
            <div className="mb-2">
              <div className="text-xs text-gray-400">Input</div>
              <pre className="whitespace-pre-wrap text-xs mt-1">{typeof span.input === 'string' ? span.input : JSON.stringify(span.input, null, 2)}</pre>
            </div>
          )}

          {span.output && (
            <div className="mb-2">
              <div className="text-xs text-gray-400">Output</div>
              <pre className="whitespace-pre-wrap text-xs mt-1">{typeof span.output === 'string' ? span.output : JSON.stringify(span.output, null, 2)}</pre>
            </div>
          )}

          {/* Children */}
          {hasChildren && (
            <div className="mt-2 space-y-1">
              {span.children.map((c: any) => (
                <SpanNode key={c.id} span={c} depth={depth + 1} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

import { usePlaygrounds } from '../lib/queries/playground';
import { Clock, CheckCircle, XCircle, Loader2, Play } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { format } from 'date-fns';

export default function PlaygroundHistory() {
  const { data: playgrounds, isLoading } = usePlaygrounds(50);
  const navigate = useNavigate();

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

                return (
                  <tr
                    key={playground.prompt_id}
                    className="hover:bg-[#252525] transition-colors cursor-pointer"
                    onClick={() => navigate(`/playground-history/${playground.prompt_id}`)}
                  >
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        {getStatusIcon(playground.status)}
                        <span className={`text-xs px-2 py-1 rounded font-medium ${getStatusColor(playground.status)}`}>
                          {playground.status}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <code className="text-sm text-gray-300 font-mono">
                        {playground.prompt_id.slice(0, 8)}
                      </code>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-white font-medium">{playground.prompt_name}</div>
                    </td>
                    <td className="px-6 py-4">
                      {playground.token_usage?.total_tokens ? (
                        <span className="text-gray-300">
                          {playground.token_usage.total_tokens.toLocaleString()}
                        </span>
                      ) : (
                        <span className="text-gray-500">-</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-gray-400">
                      {playground.created_at
                        ? format(new Date(playground.created_at), 'MMM d, HH:mm:ss')
                        : '-'}
                    </td>
                    <td className="px-6 py-4 text-gray-400">
                      {duration !== null ? `${duration}s` : '-'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

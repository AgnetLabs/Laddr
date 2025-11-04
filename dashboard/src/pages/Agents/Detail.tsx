// import { useParams } from 'react-router-dom';
// import { useAgent } from '../../lib/queries/agents';
// import { useAgentLogs } from '../../lib/hooks/useWebSocket';
// import { ArrowLeft, Activity, MessageSquare } from 'lucide-react';
// import { Link } from 'react-router-dom';
// import { format } from 'date-fns';

// export default function AgentDetail() {
//   const { agentName } = useParams<{ agentName: string }>();
//   const { data: agent, isLoading } = useAgent(agentName!);
//   const { logs, isConnected } = useAgentLogs(agentName!);

//   if (isLoading) {
//     return (
//       <div className="flex items-center justify-center h-64">
//         <p className="text-gray-400">Loading agent...</p>
//       </div>
//     );
//   }

//   if (!agent) {
//     return (
//       <div className="text-center py-12">
//         <p className="text-gray-400">Agent not found</p>
//         <Link to="/agents" className="text-primary-500 hover:text-primary-400 mt-4 inline-block">
//           Back to agents
//         </Link>
//       </div>
//     );
//   }

//   return (
//     <div className="space-y-6">
//       <div className="flex items-center gap-4">
//         <Link
//           to="/agents"
//           className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
//         >
//           <ArrowLeft className="w-5 h-5 text-gray-400" />
//         </Link>
//         <div className="flex-1">
//           <h1 className="text-2xl font-bold text-white">{agent.name}</h1>
//           <p className="text-gray-400">{agent.role}</p>
//         </div>
//       </div>

//       {/* Agent Info */}
//       <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
//         <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
//           <div className="flex items-center gap-2 mb-2">
//             <Activity className="w-5 h-5 text-primary-500" />
//             <h3 className="font-medium text-white">Status</h3>
//           </div>
//           <p className="text-2xl font-bold text-white">{agent.status}</p>
//           {agent.last_seen && (
//             <p className="text-sm text-gray-400">
//               Last seen: {format(new Date(agent.last_seen), 'MMM d, HH:mm:ss')}
//             </p>
//           )}
//         </div>

//         <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
//           <div className="flex items-center gap-2 mb-2">
//             <MessageSquare className="w-5 h-5 text-primary-500" />
//             <h3 className="font-medium text-white">Tools</h3>
//           </div>
//           <p className="text-2xl font-bold text-white">{agent.tools.length}</p>
//         </div>
//       </div>

//       {/* Agent Details */}
//       <div className="bg-gray-800 rounded-lg border border-gray-700">
//         <div className="px-6 py-4 border-b border-gray-700">
//           <h2 className="text-lg font-semibold text-white">Details</h2>
//         </div>
//         <div className="p-6 space-y-4">
//           <div>
//             <h3 className="text-sm font-medium text-gray-400 mb-1">Role</h3>
//             <p className="text-white">{agent.role}</p>
//           </div>
//           <div>
//             <h3 className="text-sm font-medium text-gray-400 mb-1">Goal</h3>
//             <p className="text-white">{agent.goal}</p>
//           </div>
//           <div>
//             <h3 className="text-sm font-medium text-gray-400 mb-1">Tools</h3>
//             <div className="flex flex-wrap gap-2">
//               {agent.tools.map((tool) => (
//                 <span
//                   key={tool}
//                   className="px-3 py-1 bg-gray-700 text-gray-300 rounded text-sm"
//                 >
//                   {tool}
//                 </span>
//               ))}
//             </div>
//           </div>
//         </div>
//       </div>

//       {/* Live Logs */}
//       <div className="bg-gray-800 rounded-lg border border-gray-700">
//         <div className="px-6 py-4 border-b border-gray-700 flex items-center justify-between">
//           <h2 className="text-lg font-semibold text-white">Live Logs</h2>
//           <div className="flex items-center gap-2">
//             <div
//               className={`w-2 h-2 rounded-full ${
//                 isConnected ? 'bg-success-500' : 'bg-error-500'
//               }`}
//             />
//             <span className="text-sm text-gray-400">
//               {isConnected ? 'Connected' : 'Disconnected'}
//             </span>
//           </div>
//         </div>
//         <div className="p-6">
//           <div className="bg-gray-900 rounded-lg p-4 font-mono text-sm max-h-96 overflow-y-auto">
//             {logs.length === 0 ? (
//               <p className="text-gray-500">No logs yet...</p>
//             ) : (
//               logs.map((log, idx) => (
//                 <div key={idx} className="mb-2">
//                   <span className="text-gray-500">
//                     {(() => { try { return format(new Date(log.timestamp), 'HH:mm:ss'); } catch { return '--:--:--'; } })()}
//                   </span>{' '}
//                   <span
//                     className={
//                       log.level === 'ERROR' || log.level === 'CRITICAL'
//                         ? 'text-error-500'
//                         : log.level === 'WARNING'
//                         ? 'text-warning-500'
//                         : 'text-gray-400'
//                     }
//                   >
//                     [{log.level}]
//                   </span>{' '}
//                   <span className="text-white">{log.message}</span>
//                 </div>
//               ))
//             )}
//           </div>
//         </div>
//       </div>
//     </div>
//   );
// }
import { useParams, Link } from 'react-router-dom';
import { useAgent } from '../../lib/queries/agents';
import { useAgentTools } from '../../lib/queries/agentTools';
import { ChevronLeft, Wrench, Search } from 'lucide-react';
import { useState } from 'react';

// Sample agent data as placeholder
const SAMPLE_AGENT = {
  name: 'Research Agent',
  role: 'AI Researcher',
  goal: 'Designed to gather, analyze, and synthesize information from various sources, acting as a sophisticated research partner',
  status: 'active',
  tools: [
    { name: 'web_search', description: 'Search the Web' },
    { name: 'web_search', description: 'Search the Web' },
    { name: 'web_search', description: 'Search the Web' },
    { name: 'web_search', description: 'Search the Web' },
    { name: 'web_search', description: 'Search the Web' },
    { name: 'web_search', description: 'Search the Web' },
    { name: 'web_search', description: 'Search the Web' }
  ],
  last_seen: new Date().toISOString()
};

export default function AgentDetail() {
  const { agentName } = useParams<{ agentName: string }>();
  const { data: agent, isLoading } = useAgent(agentName!);
  const { data: agentTools } = useAgentTools(agentName!);
  const [searchQuery, setSearchQuery] = useState('');

  // Use API data or fallback to sample data
  const displayAgent = agent || SAMPLE_AGENT;

  // Use tools from the dedicated tools endpoint if available
  const toolsList = agentTools?.tools || [];

  const filteredTools = toolsList.filter(tool =>
    tool.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    tool.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-gray-400">Loading agent...</p>
      </div>
    );
  }

  return (
    <div className=" space-y-6">
      {/* Back Button & Title */}
      <div className="flex items-center gap-3">
        <Link
          to="/agents"
          className="text-[#1FB8CD] hover:text-cyan-300 transition-colors"
        >
          <ChevronLeft className="w-5 h-5" />
        </Link>
        <h1 className="text-2xl font-semibold text-[#1FB8CD]">{displayAgent.name}</h1>
      </div>

      {/* Agent Details Card */}
      <div className="bg-[#1F2121] rounded-lg p-6 border border-gray-800">
        {/* Role Section */}
        <div className="mb-6">
          <h2 className="text-lg font-semibold text-[#1FB8CD] mb-2">Role</h2>
          <p className="text-gray-300">{displayAgent.role}</p>
        </div>

        {/* Goal Section */}
        <div className="mb-6">
          <h2 className="text-lg font-semibold text-[#1FB8CD] mb-2">Goal</h2>
          <p className="text-gray-300">{displayAgent.goal}</p>
        </div>

        {/* Tools Count */}
        <div className="flex items-center gap-2 mb-4">
          <Wrench className="w-5 h-5 text-[#1FB8CD]" />
          <span className="text-gray-300 font-medium">
            {toolsList.length > 0 ? toolsList.length : displayAgent.tools.length} tools
          </span>
        </div>

        {/* Tool Tags - Show first 8 from agent's registered tools */}
        <div className="flex flex-wrap gap-2">
          {(displayAgent.tools || []).slice(0, 8).map((tool, index) => (
            <span
              key={index}
              className="px-3 py-1 bg-[#171717] text--white rounded-lg text-sm "
            >
              {typeof tool === 'string' ? tool : tool.name}
            </span>
          ))}
        </div>
      </div>

      {/* Search Bar */}
      <div className="relative w-1/4">
        <Search className="absolute right-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-[#1FB8CD]" />
        <input
          type="text"
          placeholder="Find Tool"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full bg-[#1F2121] border border-gray-800 rounded-lg  px-4 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-[#1FB8CD]"
        />
      </div>

      {/* Tools Table */}
      <div className="bg-[#1F2121] rounded-lg border border-gray-800 overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-800">
              <th className="text-left px-6 py-4 text-sm font-medium text-gray-400">Tool Name</th>
              <th className="text-left px-6 py-4 text-sm font-medium text-gray-400">Description</th>
            </tr>
          </thead>
          <tbody>
            {filteredTools.length > 0 ? (
              filteredTools.map((tool, index) => (
                <tr key={index} className="border-b border-gray-800 hover:bg-[#252525] transition-colors">
                  <td className="px-6 py-4 text-sm text-gray-300">{tool.name}</td>
                  <td className="px-6 py-4 text-sm text-gray-400">{tool.description}</td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={2} className="px-6 py-8 text-center text-gray-500">
                  No tools found
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
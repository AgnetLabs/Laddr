import { useAgents } from '../../lib/queries/agents';
import { Wrench } from 'lucide-react';
import { Link } from 'react-router-dom';

// Sample hardcoded agents for demo
const SAMPLE_AGENTS = [
  {
    name: 'Research Agent',
    role: 'AI Researcher',
    goal: 'Designed to gather, analyze, and synthesize information from various sources, acting as a sophisticated research partner',
    status: 'active',
    tools: ['web_search', 'document_analyzer', 'data_extraction', 'summarizer', 'fact_checker', 'citation_manager', 'trend_analyzer'],
    last_seen: new Date().toISOString()
  },
  {
    name: 'Data Analyst',
    role: 'Data Scientist',
    goal: 'Specializes in processing and analyzing large datasets to extract meaningful insights and patterns',
    status: 'active',
    tools: ['data_processing', 'statistical_analysis', 'visualization', 'prediction_model', 'sql_query'],
    last_seen: new Date().toISOString()
  },
  {
    name: 'Content Writer',
    role: 'Content Creator',
    goal: 'Creates engaging, high-quality content across various formats including articles, blogs, and marketing copy',
    status: 'active',
    tools: ['text_generation', 'grammar_check', 'seo_optimizer', 'plagiarism_detector', 'style_editor', 'keyword_research'],
    last_seen: new Date().toISOString()
  },
  {
    name: 'Code Assistant',
    role: 'Software Engineer',
    goal: 'Helps developers write, debug, and optimize code across multiple programming languages and frameworks',
    status: 'active',
    tools: ['code_generator', 'debugger', 'code_review', 'unit_test_generator', 'refactoring_tool', 'documentation_generator', 'dependency_manager'],
    last_seen: new Date().toISOString()
  }
];

export default function AgentsList() {
  const { data: agents, isLoading } = useAgents();
  
  // Use sample data if no agents from API
  const displayAgents = agents && agents.length > 0 ? agents : SAMPLE_AGENTS;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-gray-400">Loading agents...</p>
      </div>
    );
  }

  return (
    <div className=" space-y-6">
      {/* Page Title */}
      <h1 className="text-2xl font-semibold text-cyan-400">Agents</h1>

      {/* Agents Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {displayAgents && displayAgents.length > 0 ? (
          displayAgents.map((agent) => (
            <Link
              key={agent.name}
              to={`/agents/${agent.name}`}
              className="bg-[#1f1f1f] rounded-lg p-6 border border-gray-800 hover:border-cyan-400 transition-colors group"
            >
              {/* Agent Title */}
              <h3 className="text-lg font-semibold text-cyan-400 mb-2 group-hover:text-cyan-300 transition-colors">
                {agent.name}
              </h3>

              {/* Agent Role */}
              <p className="text-sm text-gray-400 mb-4">{agent.role}</p>

              {/* Agent Description */}
              <p className="text-sm text-gray-300 mb-6 line-clamp-3">
                {agent.goal || 'Designed to gather, analyze, and synthesize information from various sources, acting as a sophisticated research partner'}
              </p>

              {/* Tools Count */}
              <div className="flex items-center gap-2 text-sm text-gray-400">
                <Wrench className="w-4 h-4 text-cyan-400" />
                <span>{agent.tools?.length || 0} tools</span>
              </div>
            </Link>
          ))
        ) : (
          <div className="col-span-full text-center py-12">
            <p className="text-gray-400">No agents configured</p>
          </div>
        )}
      </div>
    </div>
  );
}
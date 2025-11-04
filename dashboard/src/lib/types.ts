// API Response Types

export interface HealthStatus {
  status: string;
  version: string;
  components: {
    database: string;
    storage: string;
    message_bus: string;
  };
}

export interface Agent {
  name: string;
  role: string;
  goal: string;
  status: string;
  tools: string[];
  last_seen?: string;
  trace_count: number;
  last_executed?: string;
}

// AgentQueueInfo removed - not available in v3.0 API

export interface Job {
  job_id: string;
  pipeline_name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  created_at?: string;
  completed_at?: string;
  inputs?: Record<string, any>;
  outputs?: Record<string, any>;
  error?: string | null;
  agent?: string;
  result?: any;
  duration_ms?: number;
  token_usage?: {
    prompt_tokens?: number;
    completion_tokens?: number;
    total_tokens?: number;
    by_model?: Array<{
      provider?: string | null;
      model?: string | null;
      prompt_tokens?: number;
      completion_tokens?: number;
      total_tokens?: number;
      calls?: number;
    }>;
  };
}

export interface PipelineRunRequest {
  pipeline_name: string;
  inputs?: Record<string, any>;
}

export interface Trace {
  id: string;
  job_id?: string;
  agent_name?: string;
  event_type: string;
  payload: Record<string, any>;
  timestamp: string;
  // Optional: present when UI should nest this trace under a parent (e.g., delegate_parallel)
  parent_trace_id?: number | string;
}

export interface Metric {
  name: string;
  value: number;
  timestamp: string;
  labels: Record<string, string>;
  type: 'counter' | 'gauge' | 'histogram';
}

export interface SystemMetrics {
  total_jobs: number;
  avg_latency_ms: number;
  active_agents_count: number;
  cache_hits: number;
  tool_calls: number;
  total_tokens: number;
  completed_jobs: number;
  failed_jobs: number;
  timestamp: string;
  // Optional fields from certain deployments
  total_prompts?: number;
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: string;
}

export interface ChatRequest {
  message: string;
  context?: Record<string, any>;
}

export interface ChatResponse {
  task_id: string;
  status: string;
  response?: string;
}

export interface LogMessage {
  timestamp: string;
  level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL';
  agent_name: string;
  message: string;
  metadata?: Record<string, any>;
}

export interface SystemEvent {
  event_type: 'agent_started' | 'agent_stopped' | 'job_submitted' | 'job_completed' | 'job_failed' | 'error';
  timestamp: string;
  data: Record<string, any>;
}

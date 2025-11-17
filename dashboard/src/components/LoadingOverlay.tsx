import { Loader2 } from 'lucide-react';

interface LoadingOverlayProps {
  isLoading: boolean;
  message?: string;
  progress?: {
    current: number;
    total: number;
  };
}

export default function LoadingOverlay({ isLoading, message, progress }: LoadingOverlayProps) {
  if (!isLoading) return null;

  const progressPercent = progress ? Math.round((progress.current / progress.total) * 100) : null;

  return (
    <div 
      className="fixed inset-0 z-[9999] flex items-center justify-center bg-[#191A1A]/95 backdrop-blur-sm"
      style={{ pointerEvents: 'auto' }}
      onClick={(e) => e.stopPropagation()}
      onMouseDown={(e) => e.stopPropagation()}
    >
      <div className="flex flex-col items-center gap-4">
        <Loader2 className="w-12 h-12 text-[#1FB8CD] animate-spin" />
        <div className="text-center">
          <h3 className="text-lg font-semibold text-white mb-2">
            {message || 'Loading agents and tools...'}
          </h3>
          {progress && (
            <div className="w-64 mx-auto">
              <div className="flex items-center justify-between text-sm text-gray-400 mb-2">
                <span>Loading tools for {progress.current} of {progress.total} agents</span>
                <span>{progressPercent}%</span>
              </div>
              <div className="w-full bg-[#1F2121] rounded-full h-2 border border-gray-800">
                <div
                  className="bg-[#1FB8CD] h-2 rounded-full transition-all duration-300"
                  style={{ width: `${progressPercent}%` }}
                />
              </div>
            </div>
          )}
          <p className="text-sm text-gray-400 mt-4">
            Please wait while we connect to MCP servers and discover tools...
          </p>
        </div>
      </div>
    </div>
  );
}


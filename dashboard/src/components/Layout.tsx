import { ReactNode } from 'react';
import Header from './Header';
import Sidebar from './Sidebar';
import LoadingOverlay from './LoadingOverlay';
import { useAgentsAndToolsLoading } from '../lib/hooks/useAgentsAndToolsLoading';

interface LayoutProps {
  children: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const { isLoading, agentsCount, loadedToolsCount } = useAgentsAndToolsLoading();

  return (
    <div className="flex h-screen bg-[#191A1A] relative">
      <LoadingOverlay
        isLoading={isLoading}
        message="Loading agents and MCP tools..."
        progress={
          agentsCount > 0
            ? {
                current: loadedToolsCount,
                total: agentsCount,
              }
            : undefined
        }
      />
      <Sidebar />
      <div className="flex-1 flex flex-col border-l border-[#1F2121] overflow-hidden">
        <Header />
        <main className="flex-1 overflow-y-auto p-6">
          {children}
        </main>
      </div>
    </div>
  );
}

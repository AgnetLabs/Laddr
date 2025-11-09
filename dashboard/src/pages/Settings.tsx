import { Settings as SettingsIcon, Server, Database, Zap } from 'lucide-react';
import { useHealth } from '../lib/queries/health';
import { getApiDocsUrl } from '../lib/config';

export default function Settings() {
  const { data: health } = useHealth();

  return (
    <div className="space-y-6 bg-[#191A1A] min-h-screen">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="p-2 bg-[#1F2121] rounded-lg">
          <SettingsIcon className="w-7 h-7 text-[#1FB8CD]" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white">Settings</h1>
          <p className="text-sm text-gray-400">System configuration and information</p>
        </div>
      </div>

      {/* System Info Card */}
      <div className="bg-[#1F2121] rounded-xl border border-[#2A2C2C] shadow-sm">
        <div className="px-6 py-4 border-b border-[#2A2C2C]">
          <h2 className="text-lg font-semibold text-white">System Information</h2>
        </div>
        <div className="p-6 space-y-4">
          {[
            { icon: Server, label: 'Version', value: health?.version || 'Unknown' },
            { icon: Database, label: 'Database', value: health?.components?.database || 'Unknown' },
            { icon: Zap, label: 'Storage', value: health?.components?.storage || 'Unknown' },
            { icon: Server, label: 'Message Bus', value: health?.components?.message_bus || 'Unknown' },
          ].map(({ icon: Icon, label, value }, i, arr) => (
            <div
              key={label}
              className={`flex items-center justify-between py-3 ${
                i < arr.length - 1 ? 'border-b border-[#2A2C2C]' : ''
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon className="w-5 h-5 text-[#1FB8CD]" />
                <span className="text-gray-300">{label}</span>
              </div>
              <span className="text-white font-mono">{value}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Service Links */}
      <div className="bg-[#1F2121] rounded-xl border border-[#2A2C2C] shadow-sm">
        <div className="px-6 py-4 border-b border-[#2A2C2C]">
          <h2 className="text-lg font-semibold text-white">Service Links</h2>
        </div>
        <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            {
              title: 'API Documentation',
              desc: 'FastAPI interactive docs',
              href: getApiDocsUrl(),
            },
            {
              title: 'MinIO Console',
              desc: 'Storage management',
              href: 'http://localhost:9001',
            },
          ].map((link) => (
            <a
              key={link.title}
              href={link.href}
              target="_blank"
              rel="noopener noreferrer"
              className="bg-[#191A1A] hover:bg-[#232525] border border-[#2A2C2C] rounded-lg p-4 transition-all duration-150 hover:shadow-md hover:border-cyan-500/30"
            >
              <h3 className="text-white font-semibold mb-1">{link.title}</h3>
              <p className="text-sm text-gray-400">{link.desc}</p>
            </a>
          ))}
        </div>
      </div>
    </div>
  );
}

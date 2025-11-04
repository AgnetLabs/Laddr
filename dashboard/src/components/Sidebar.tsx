import { NavLink, useNavigate } from 'react-router-dom';
import { Home, Users, Briefcase, Play, Clock, GitBranch, Terminal, Settings, LogOut } from 'lucide-react';
import { logout, getCurrentUser } from '../lib/auth';

const navigation = [
  { name: 'Dashboard', href: '/', icon: Home },
  { name: 'Agents', href: '/agents', icon: Users },
  { name: 'Playground', href: '/playground', icon: Play },
  { name: 'Playground History', href: '/playground-history', icon: Clock },
  { name: 'Traces', href: '/traces', icon: GitBranch },
  { name: 'Logs', href: '/logs', icon: Terminal },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export default function Sidebar() {
  const navigate = useNavigate();
  const user = getCurrentUser();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="w-64 h-screen bg-[#191A1A] flex flex-col">
      {/* Top Section (same height as header) */}
      <div className="h-14 flex items-center pt-1 px-3 border-b border-[#1F2121]">
        <div className="w-[6.5rem] h-[6.5rem] flex items-center justify-center">
          <img src="/laddr.svg" alt="Laddr Logo" />
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 mt-2">
        {navigation.map((item) => (
          <NavLink
            key={item.name}
            to={item.href}
            end={item.href === '/'}
            className={({ isActive }) =>
              `w-full flex items-center gap-3 px-4 py-3 mb-1 rounded-lg transition-all duration-150 ${
                isActive
                  ? 'bg-[#1F2121] border border-[#2A2C2C] text-cyan-400 shadow-sm'
                  : 'text-gray-400 hover:text-white hover:bg-[#252525]'
              }`
            }
          >
            <item.icon className="w-5 h-5" />
            <span className="text-sm font-medium">{item.name}</span>
          </NavLink>
        ))}
      </nav>

      {/* User Profile */}
      <div className="p-4 border-t border-[#1F2121]">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-[#191A1A] flex items-center justify-center overflow-hidden">
            <img
              src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%23888'%3E%3Cpath d='M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z'/%3E%3C/svg%3E"
              alt="User"
              className="w-full h-full"
            />
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-sm font-medium text-white truncate">{user?.username || 'Guest User'}</div>
            {/* <div className="text-xs text-gray-400 truncate">{'guest@example.com'}</div> */}
          </div>
          <button
            onClick={handleLogout}
            className="text-gray-400 hover:text-red-400 transition-colors"
            title="Logout"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

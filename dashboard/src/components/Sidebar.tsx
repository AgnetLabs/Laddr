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
      <div className="h-14 flex items-center px-3 border-b border-[#1F2121]">
        <div className="w-12 h-12 flex items-center justify-center">
          <svg width="61" height="61" viewBox="0 0 41 41" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M0 6.61364C0 2.96103 2.96103 0 6.61364 0H33.8864C37.539 0 40.5 2.96103 40.5 6.61364V33.8864C40.5 37.539 37.539 40.5 33.8864 40.5H6.61364C2.96103 40.5 0 37.539 0 33.8864V6.61364Z" fill="#191A1A"/>
            <g clipPath="url(#clip0_86_4639)">
              <path d="M31.4948 9.00521H9.00525V31.4948H31.4948V9.00521Z" fill="#181919" stroke="#231F20" strokeWidth="0.0104118" strokeMiterlimit="10"/>
              <path d="M24.1832 14.0791V26.3934H16.7946V23.9306H21.7204V16.5419H16.7946V14.0791H24.1832Z" fill="#F9F9FA"/>
              <path d="M19.2576 19.0047V21.4678H14.3317V26.3934H11.8689V19.0047H19.2576Z" fill="#F9F9FA"/>
              <path d="M28.6311 23.9021H26.1123V26.4209H28.6311V23.9021Z" fill="#F9F9FA"/>
            </g>
            <defs>
              <clipPath id="clip0_86_4639">
                <rect width="22.5" height="22.5" fill="white" transform="translate(9 9)"/>
              </clipPath>
            </defs>
          </svg>
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

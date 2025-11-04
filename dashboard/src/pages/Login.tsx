import { useState, FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { LogIn } from 'lucide-react';
import { login } from '../lib/auth';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    setError('');

    if (login(username, password)) {
      navigate('/');
    } else {
      setError('Invalid username or password');
    }
  };

  return (
    <div className="min-h-screen bg-[#1a1a1a] flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="bg-[#1F2121] rounded-lg border border-gray-800 p-8">
          {/* Logo Section */}
          <div className="flex items-center justify-center mb-4">
            <div className="w-12 h-12 rounded flex items-center justify-center">
<svg width="61" height="61" viewBox="0 0 41 41" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M0 6.61364C0 2.96103 2.96103 0 6.61364 0H33.8864C37.539 0 40.5 2.96103 40.5 6.61364V33.8864C40.5 37.539 37.539 40.5 33.8864 40.5H6.61364C2.96103 40.5 0 37.539 0 33.8864V6.61364Z" fill="#191A1A"/>
<g clip-path="url(#clip0_86_4639)">
<path d="M31.4948 9.00521H9.00525V31.4948H31.4948V9.00521Z" fill="#181919" stroke="#231F20" stroke-width="0.0104118" stroke-miterlimit="10"/>
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

          {/* Title */}
          <div className="text-center mb-8">
            <h1 className="text-2xl font-semibold text-white mb-2">Welcome Back</h1>
            <p className="text-sm text-gray-400">Sign in to your account</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="bg-red-500/10 border border-red-500/50 text-red-400 px-4 py-3 rounded-lg text-sm">
                {error}
              </div>
            )}

            <div>
              <label htmlFor="username" className="block text-sm font-medium text-white mb-2">
                Username
              </label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full px-4 py-3 bg-[#171717] border border-gray-800 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:border-transparent transition-all"
                placeholder="Enter your username"
                required
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-white mb-2">
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 bg-[#171717] border border-gray-800 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:border-transparent transition-all"
                placeholder="Enter your password"
                required
              />
            </div>

            <button
              type="submit"
              className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-[#1FB8CD] hover:bg-cyan-500 text-black font-semibold rounded-lg transition-colors"
            >
              <LogIn className="w-5 h-5" />
              Sign In
            </button>
          </form>

          <div className="mt-6 pt-6 border-t border-gray-800">
            <p className="text-center text-sm text-gray-400">
              Default credentials: <span className="text-[#1FB8CD] font-medium">admin / admin</span>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
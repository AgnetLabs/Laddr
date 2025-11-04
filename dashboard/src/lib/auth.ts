import Cookies from 'js-cookie';

const AUTH_COOKIE = 'laddr_auth';

export interface AuthUser {
  username: string;
  authenticated: boolean;
}

export const login = (username: string, password: string): boolean => {
  // Parse DASH_USERS from environment (format: "user1:pass1,user2:pass2")
  const dashUsers = import.meta.env.VITE_DASH_USERS || 'admin:admin';
  const userPairs = dashUsers.split(',').map((pair: string) => {
    const [u, p] = pair.split(':');
    return { username: u?.trim(), password: p?.trim() };
  });

  const validUser = userPairs.find(
    (u) => u.username === username && u.password === password
  );

  if (validUser) {
    const token = btoa(`${username}:${Date.now()}`);
    Cookies.set(AUTH_COOKIE, token, { expires: 7 }); // 7 days
    localStorage.setItem('auth_token', token);
    localStorage.setItem('auth_user', username);
    return true;
  }

  return false;
};

export const logout = () => {
  Cookies.remove(AUTH_COOKIE);
  localStorage.removeItem('auth_token');
  localStorage.removeItem('auth_user');
};

export const isAuthenticated = (): boolean => {
  return !!Cookies.get(AUTH_COOKIE);
};

export const getCurrentUser = (): AuthUser | null => {
  const token = Cookies.get(AUTH_COOKIE);
  const username = localStorage.getItem('auth_user');

  if (token && username) {
    return {
      username,
      authenticated: true,
    };
  }

  return null;
};

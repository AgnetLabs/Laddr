import { useLocation, Link } from 'react-router-dom';
import { ChevronRight } from 'lucide-react';

export default function Header() {
  const location = useLocation();

  const getBreadcrumbs = () => {
    const paths = location.pathname.split('/').filter(Boolean);
    const breadcrumbs = [{ name: 'Home', path: '/' }];

    let currentPath = '';
    paths.forEach((segment) => {
      currentPath += `/${segment}`;
      const decodedSegment = decodeURIComponent(segment); // ✅ Decode "%20" → " "
      const name = decodedSegment
        .split('-')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
      breadcrumbs.push({ name, path: currentPath });
    });

    return breadcrumbs;
  };

  const breadcrumbs = getBreadcrumbs();

  return (
    <header className="h-14 bg-[#191A1A] border-b border-gray-800 flex items-center px-6">
      <nav className="flex items-center gap-2 text-sm">
        {breadcrumbs.map((crumb, index) => (
          <div key={crumb.path} className="flex items-center gap-2">
            {index === breadcrumbs.length - 1 ? (
              <span className="text-cyan-400 font-medium">{crumb.name}</span>
            ) : (
              <>
                <Link
                  to={crumb.path}
                  className="text-gray-400 hover:text-gray-300 transition-colors"
                >
                  {crumb.name}
                </Link>
                <ChevronRight className="w-4 h-4 text-gray-500" />
              </>
            )}
          </div>
        ))}
      </nav>
    </header>
  );
}

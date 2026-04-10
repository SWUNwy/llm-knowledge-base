import { useState, type FormEvent } from 'react';
import { useNavigate, Navigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { cloudLogin } from '../services/cloudApi';
import { Brain } from 'lucide-react';
import ErrorAlert from '../components/ErrorAlert';

export default function Login() {
  const { user, login } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // Redirect if already logged in
  if (user) {
    return <Navigate to="/library" replace />;
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const result = await cloudLogin(email, password);

      // Store tokens
      localStorage.setItem('access_token', result.access_token);
      if (result.license_token) {
        localStorage.setItem('license_token', result.license_token);
      }
      localStorage.setItem('user_tier', result.tier || 'trial');
      localStorage.setItem('user_email', result.user?.email || '');

      // Update auth state
      await login(result.access_token);

      // Redirect to main app
      navigate('/library');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = () => {
    // Open browser to registration page
    window.open('https://knowledgebase.ai/register', '_blank');
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <Brain className="w-10 h-10 text-blue-600 mx-auto mb-3" />
          <h1 className="text-2xl font-bold text-gray-900">
            KnowledgeBase
          </h1>
          <p className="text-gray-500 mt-1">Sign in to continue</p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-4"
        >
          {error && (
            <ErrorAlert error={new Error(error)} variant="inline" />
          )}

          <div>
            <label
              htmlFor="email"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label
              htmlFor="password"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
              autoComplete="current-password"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2 px-4 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <div className="mt-4 text-center text-sm">
          <span className="text-gray-600">Don't have an account? </span>
          <button
            type="button"
            onClick={handleRegister}
            className="text-blue-600 hover:text-blue-700 font-medium"
          >
            Sign Up
          </button>
        </div>
      </div>
    </div>
  );
}

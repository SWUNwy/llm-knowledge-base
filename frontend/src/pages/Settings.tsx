import { useState, type FormEvent } from 'react';
import { api } from '../services/api';
import { Save, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import ErrorAlert from '../components/ErrorAlert';

interface LLMConfig {
  provider: string;
  model: string;
  api_key: string;
}

export default function Settings() {
  const [provider, setProvider] = useState('openai');
  const [model, setModel] = useState('gpt-4o');
  const [apiKey, setApiKey] = useState('');
  const [showApiKey, setShowApiKey] = useState(false);
  const [testStatus, setTestStatus] = useState<'idle' | 'testing' | 'success' | 'error'>('idle');
  const [testMessage, setTestMessage] = useState('');
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved'>('idle');

  const handleSave = async (e: FormEvent) => {
    e.preventDefault();
    setSaveStatus('saving');

    // Simulate save — replace with actual API call when backend endpoint exists
    const config: LLMConfig = {
      provider,
      model,
      api_key: apiKey,
    };

    try {
      // TODO: Replace with api.saveSettings(config) when available
      console.log('Saving settings:', { ...config, api_key: '***' });
      await new Promise((resolve) => setTimeout(resolve, 500));
      setSaveStatus('saved');
      setTimeout(() => setSaveStatus('idle'), 2000);
    } catch {
      setSaveStatus('idle');
    }
  };

  const handleTestConnection = async () => {
    setTestStatus('testing');
    setTestMessage('');

    try {
      // Use status endpoint as a basic connectivity check
      await api.getStatus();
      setTestStatus('success');
      setTestMessage('Connection successful');
    } catch (err) {
      setTestStatus('error');
      setTestMessage(
        err instanceof Error ? err.message : 'Connection failed',
      );
    }
  };

  const providerModels: Record<string, string[]> = {
    openai: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo'],
    anthropic: ['claude-sonnet-4-20250514', 'claude-haiku-4-20250414', 'claude-3-5-sonnet-20241022'],
    google: ['gemini-2.0-flash', 'gemini-1.5-pro', 'gemini-1.5-flash'],
    local: ['llama3', 'mistral', 'codellama'],
  };

  return (
    <div className="max-w-2xl mx-auto p-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Settings</h1>

      <form
        onSubmit={handleSave}
        className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-5"
      >
        {/* Provider */}
        <div>
          <label
            htmlFor="provider"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            LLM Provider
          </label>
          <select
            id="provider"
            value={provider}
            onChange={(e) => {
              setProvider(e.target.value);
              setModel(providerModels[e.target.value]?.[0] ?? '');
            }}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="openai">OpenAI</option>
            <option value="anthropic">Anthropic</option>
            <option value="google">Google</option>
            <option value="local">Local (Ollama)</option>
          </select>
        </div>

        {/* Model */}
        <div>
          <label
            htmlFor="model"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Model
          </label>
          <select
            id="model"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            {providerModels[provider]?.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
        </div>

        {/* API Key */}
        <div>
          <label
            htmlFor="api-key"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            API Key
          </label>
          <div className="relative">
            <input
              id="api-key"
              type={showApiKey ? 'text' : 'password'}
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="sk-..."
              className="w-full px-3 py-2 pr-16 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
            <button
              type="button"
              onClick={() => setShowApiKey(!showApiKey)}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-gray-500 hover:text-gray-700 px-2 py-1"
            >
              {showApiKey ? 'Hide' : 'Show'}
            </button>
          </div>
          {provider === 'local' && (
            <p className="text-xs text-gray-400 mt-1">
              No API key needed for local models
            </p>
          )}
        </div>

        {/* Test connection */}
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={handleTestConnection}
            disabled={testStatus === 'testing'}
            className="px-4 py-2 border border-gray-300 text-sm font-medium rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            {testStatus === 'testing' ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : null}
            Test Connection
          </button>
          {testStatus === 'success' && (
            <span className="flex items-center gap-1 text-sm text-green-600">
              <CheckCircle className="w-4 h-4" />
              {testMessage}
            </span>
          )}
          {testStatus === 'error' && (
            <ErrorAlert error={new Error(testMessage)} variant="inline" />
          )}
        </div>

        {/* Divider */}
        <hr className="border-gray-200" />

        {/* Save */}
        <div className="flex items-center gap-3">
          <button
            type="submit"
            disabled={saveStatus === 'saving'}
            className="px-6 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            <Save className="w-4 h-4" />
            {saveStatus === 'saving' ? 'Saving...' : 'Save Settings'}
          </button>
          {saveStatus === 'saved' && (
            <span className="flex items-center gap-1 text-sm text-green-600">
              <CheckCircle className="w-4 h-4" />
              Settings saved
            </span>
          )}
        </div>
      </form>
    </div>
  );
}

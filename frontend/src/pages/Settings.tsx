import { useState, useEffect, type FormEvent } from 'react';
import { api, type SettingsResponse } from '../services/api';
import { getUsage } from '../services/cloudApi';
import { Save, CheckCircle, Loader2 } from 'lucide-react';
import ErrorAlert from '../components/ErrorAlert';

const PROVIDER_MODEL_MAP: Record<string, string[]> = {
  openai: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo'],
  anthropic: ['claude-sonnet-4-20250514', 'claude-haiku-4-20250414', 'claude-3-5-sonnet-20241022'],
  google: ['gemini-2.0-flash', 'gemini-1.5-pro', 'gemini-1.5-flash'],
  local: ['llama3', 'mistral', 'codellama'],
};

function parseModelString(model: string): { provider: string; model: string } {
  const parts = model.split('/');
  if (parts.length >= 2) {
    const provider = parts[0];
    const modelName = parts.slice(1).join('/');
    if (provider in PROVIDER_MODEL_MAP) {
      return { provider, model: modelName };
    }
  }
  return { provider: 'openai', model };
}

export default function Settings() {
  const [provider, setProvider] = useState('openai');
  const [model, setModel] = useState('gpt-4o');
  const [apiKey, setApiKey] = useState('');
  const [showApiKey, setShowApiKey] = useState(false);
  const [testStatus, setTestStatus] = useState<'idle' | 'testing' | 'success' | 'error'>('idle');
  const [testMessage, setTestMessage] = useState('');
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved'>('idle');
  const [loadError, setLoadError] = useState<string | null>(null);

  const [tier] = useState<string>(localStorage.getItem('user_tier') || 'trial');
  const [usage, setUsage] = useState<{ compile: number; qa: number } | null>(null);

  // Load current settings from backend
  useEffect(() => {
    api.getSettings()
      .then((data: SettingsResponse) => {
        const parsed = parseModelString(data.llm_default_model);
        setProvider(parsed.provider);
        setModel(parsed.model);

        // Show masked key if provider is configured
        const providerConfig = data.llm_providers[parsed.provider === 'google' ? 'gemini' : parsed.provider];
        if (providerConfig?.key) {
          setApiKey(providerConfig.key);
        }
      })
      .catch((err) => {
        setLoadError(err instanceof Error ? err.message : 'Failed to load settings');
      });
  }, []);

  // Load cloud usage if applicable
  useEffect(() => {
    const licenseToken = localStorage.getItem('license_token');
    if (licenseToken) {
      getUsage(licenseToken).then((data) => setUsage({ compile: data.usage.compile, qa: data.usage.qa })).catch(console.error);
    }
  }, []);

  const handleSave = async (e: FormEvent) => {
    e.preventDefault();
    setSaveStatus('saving');

    try {
      await api.saveSettings({
        llm_default_model: `${provider}/${model}`,
        ...(provider === 'openai' && apiKey ? { openai_api_key: apiKey } : {}),
        ...(provider === 'anthropic' && apiKey ? { anthropic_api_key: apiKey } : {}),
        ...(provider === 'google' && apiKey ? { gemini_api_key: apiKey } : {}),
        ...(provider === 'local' && apiKey ? { ollama_base_url: apiKey } : {}),
      });
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
      const result = await api.verifyLLM({
        model: `${provider}/${model}`,
        ...(provider !== 'local' && apiKey ? { api_key: apiKey } : {}),
        ...(provider === 'local' && apiKey ? { base_url: apiKey } : {}),
      });

      if (result.success) {
        setTestStatus('success');
        setTestMessage(`${result.message}${result.latency_ms ? ` (${result.latency_ms}ms)` : ''}`);
      } else {
        setTestStatus('error');
        setTestMessage(result.message);
      }
    } catch (err) {
      setTestStatus('error');
      setTestMessage(err instanceof Error ? err.message : 'Connection failed');
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Settings</h1>

      {/* Plan and Usage Section */}
      <div className="mb-8 p-6 bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl border border-blue-200">
        <h2 className="text-xl font-semibold mb-4">Current Plan</h2>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-2xl font-bold capitalize text-gray-900">{tier}</p>
            {usage && (
              <p className="text-sm text-gray-600 mt-1">
                This month: {usage.compile} compilations, {usage.qa} Q&A
              </p>
            )}
          </div>
          <button
            onClick={() => window.open('https://knowledgebase.ai/dashboard', '_blank')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
          >
            Manage Plan
          </button>
        </div>
      </div>

      {loadError && <ErrorAlert error={new Error(loadError)} variant="inline" />}

      <form
        onSubmit={handleSave}
        className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-5"
      >
        {/* Provider */}
        <div>
          <label htmlFor="provider" className="block text-sm font-medium text-gray-700 mb-1">
            LLM Provider
          </label>
          <select
            id="provider"
            value={provider}
            onChange={(e) => {
              setProvider(e.target.value);
              setModel(PROVIDER_MODEL_MAP[e.target.value]?.[0] ?? '');
              setApiKey('');
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
          <label htmlFor="model" className="block text-sm font-medium text-gray-700 mb-1">
            Model
          </label>
          <select
            id="model"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            {PROVIDER_MODEL_MAP[provider]?.map((m) => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
        </div>

        {/* API Key / Base URL */}
        <div>
          <label htmlFor="api-key" className="block text-sm font-medium text-gray-700 mb-1">
            {provider === 'local' ? 'Base URL' : 'API Key'}
          </label>
          <div className="relative">
            <input
              id="api-key"
              type={showApiKey ? 'text' : 'password'}
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder={provider === 'local' ? 'http://localhost:11434' : 'sk-...'}
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
            <p className="text-xs text-gray-400 mt-1">No API key needed for local models</p>
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
            {testStatus === 'testing' && <Loader2 className="w-4 h-4 animate-spin" />}
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

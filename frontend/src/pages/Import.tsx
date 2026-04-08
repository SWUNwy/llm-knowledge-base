import { useState, type FormEvent } from 'react';
import { useMutation } from '@tanstack/react-query';
import { api, type IngestResponse } from '../services/api';
import { Upload, FileText, Link, Tag, CheckCircle, XCircle } from 'lucide-react';

export default function Import() {
  const [url, setUrl] = useState('');
  const [filePath, setFilePath] = useState('');
  const [tags, setTags] = useState('');
  const [recentImports, setRecentImports] = useState<IngestResponse[]>([]);

  const ingestUrlMutation = useMutation({
    mutationFn: (vars: { url: string; tags: string[] }) =>
      api.ingestUrl(vars.url, vars.tags),
    onSuccess: (data) => {
      setRecentImports((prev) => [data, ...prev]);
      setUrl('');
      setTags('');
    },
  });

  const ingestFileMutation = useMutation({
    mutationFn: (vars: { path: string; tags: string[] }) =>
      api.ingestFile(vars.path, vars.tags),
    onSuccess: (data) => {
      setRecentImports((prev) => [data, ...prev]);
      setFilePath('');
      setTags('');
    },
  });

  const parsedTags = tags
    .split(',')
    .map((t) => t.trim())
    .filter(Boolean);

  const handleUrlSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    ingestUrlMutation.mutate({ url: url.trim(), tags: parsedTags });
  };

  const handleFileSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!filePath.trim()) return;
    ingestFileMutation.mutate({ path: filePath.trim(), tags: parsedTags });
  };

  return (
    <div className="max-w-3xl mx-auto p-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Import</h1>

      <div className="grid gap-6 md:grid-cols-2">
        {/* URL Import */}
        <form
          onSubmit={handleUrlSubmit}
          className="bg-white rounded-xl shadow-sm border border-gray-200 p-5 space-y-4"
        >
          <div className="flex items-center gap-2 text-gray-900 font-medium">
            <Link className="w-5 h-5 text-blue-600" />
            Import from URL
          </div>

          <div>
            <label
              htmlFor="url-input"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              URL
            </label>
            <input
              id="url-input"
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://example.com/article"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label
              htmlFor="url-tags"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Tags (comma separated)
            </label>
            <div className="relative">
              <Tag className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                id="url-tags"
                type="text"
                value={tags}
                onChange={(e) => setTags(e.target.value)}
                placeholder="web, article, research"
                className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={ingestUrlMutation.isPending}
            className="w-full py-2 px-4 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
          >
            <Upload className="w-4 h-4" />
            {ingestUrlMutation.isPending ? 'Importing...' : 'Import URL'}
          </button>

          {ingestUrlMutation.isError && (
            <p className="text-sm text-red-600">
              {ingestUrlMutation.error instanceof Error
                ? ingestUrlMutation.error.message
                : 'Import failed'}
            </p>
          )}
        </form>

        {/* File Import */}
        <form
          onSubmit={handleFileSubmit}
          className="bg-white rounded-xl shadow-sm border border-gray-200 p-5 space-y-4"
        >
          <div className="flex items-center gap-2 text-gray-900 font-medium">
            <FileText className="w-5 h-5 text-blue-600" />
            Import from File
          </div>

          <div>
            <label
              htmlFor="file-input"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              File Path
            </label>
            <input
              id="file-input"
              type="text"
              value={filePath}
              onChange={(e) => setFilePath(e.target.value)}
              placeholder="/path/to/document.pdf"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label
              htmlFor="file-tags"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Tags (comma separated)
            </label>
            <div className="relative">
              <Tag className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                id="file-tags"
                type="text"
                value={tags}
                onChange={(e) => setTags(e.target.value)}
                placeholder="pdf, paper, research"
                className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={ingestFileMutation.isPending}
            className="w-full py-2 px-4 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
          >
            <Upload className="w-4 h-4" />
            {ingestFileMutation.isPending ? 'Importing...' : 'Import File'}
          </button>

          {ingestFileMutation.isError && (
            <p className="text-sm text-red-600">
              {ingestFileMutation.error instanceof Error
                ? ingestFileMutation.error.message
                : 'Import failed'}
            </p>
          )}
        </form>
      </div>

      {/* Recent Imports */}
      {recentImports.length > 0 && (
        <div className="mt-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">
            Recent Imports
          </h2>
          <div className="space-y-2">
            {recentImports.map((item, idx) => (
              <div
                key={idx}
                className="flex items-center gap-3 bg-white rounded-lg border border-gray-200 px-4 py-3"
              >
                {item.success ? (
                  <CheckCircle className="w-5 h-5 text-green-500 shrink-0" />
                ) : (
                  <XCircle className="w-5 h-5 text-red-500 shrink-0" />
                )}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {item.title ?? item.path ?? 'Untitled'}
                  </p>
                  {item.error && (
                    <p className="text-xs text-red-600 truncate">{item.error}</p>
                  )}
                </div>
                {item.doc_id && (
                  <span className="text-xs text-gray-400 font-mono">
                    {item.doc_id.slice(0, 8)}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

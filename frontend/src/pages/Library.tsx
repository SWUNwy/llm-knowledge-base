import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api, type DocumentSummary } from '../services/api';
import { Search, FileText, BookOpen, Video, Code, Filter } from 'lucide-react';
import ErrorAlert from '../components/ErrorAlert';

const typeIcons: Record<string, typeof FileText> = {
  web: FileText,
  paper: BookOpen,
  video: Video,
  code: Code,
};

const statusColors: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  processed: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
};

export default function Library() {
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [page, setPage] = useState(1);

  const { data, isLoading, error } = useQuery({
    queryKey: ['documents', { search, page }],
    queryFn: () => api.getDocuments({ search: search || undefined, page, limit: 20 }),
  });

  const filteredItems = data?.items?.filter((doc: DocumentSummary) => {
    if (typeFilter && doc.type !== typeFilter) return false;
    if (statusFilter && doc.status !== statusFilter) return false;
    return true;
  });

  return (
    <div className="max-w-5xl mx-auto p-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Library</h1>

      {/* Search and filters */}
      <div className="flex flex-wrap gap-3 mb-6">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            placeholder="Search documents..."
            className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        <div className="relative">
          <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="pl-9 pr-8 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 appearance-none"
          >
            <option value="">All Types</option>
            <option value="web">Web</option>
            <option value="paper">Paper</option>
            <option value="video">Video</option>
            <option value="code">Code</option>
          </select>
        </div>

        <div className="relative">
          <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="pl-9 pr-8 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 appearance-none"
          >
            <option value="">All Statuses</option>
            <option value="pending">Pending</option>
            <option value="processed">Processed</option>
            <option value="failed">Failed</option>
          </select>
        </div>
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="text-center py-12 text-gray-500">
          Loading documents...
        </div>
      )}

      {/* Error */}
      {error && (
        <ErrorAlert error={error} variant="card" onRetry={() => {}} />
      )}

      {/* Document list */}
      {data && (
        <>
          <p className="text-sm text-gray-500 mb-3">
            {data.total} document{data.total !== 1 ? 's' : ''} total
          </p>

          {filteredItems && filteredItems.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              No documents found
            </div>
          ) : (
            <div className="space-y-2">
              {filteredItems?.map((doc: DocumentSummary) => {
                const Icon = typeIcons[doc.type] ?? FileText;
                return (
                  <div
                    key={doc.id}
                    className="flex items-center gap-4 bg-white rounded-lg border border-gray-200 px-4 py-3 hover:border-gray-300 transition-colors cursor-pointer"
                  >
                    <Icon className="w-5 h-5 text-gray-400 shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {doc.title}
                      </p>
                      <div className="flex items-center gap-2 mt-1">
                        {doc.tags.map((tag) => (
                          <span
                            key={tag}
                            className="inline-block text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    </div>
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full font-medium ${statusColors[doc.status] ?? 'bg-gray-100 text-gray-600'}`}
                    >
                      {doc.status}
                    </span>
                    <span className="text-xs text-gray-400 whitespace-nowrap">
                      {new Date(doc.created_at).toLocaleDateString()}
                    </span>
                  </div>
                );
              })}
            </div>
          )}

          {/* Pagination */}
          {data.total > data.limit && (
            <div className="flex items-center justify-center gap-4 mt-6">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <span className="text-sm text-gray-500">Page {page}</span>
              <button
                onClick={() => setPage((p) => p + 1)}
                disabled={page * data.limit >= data.total}
                className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

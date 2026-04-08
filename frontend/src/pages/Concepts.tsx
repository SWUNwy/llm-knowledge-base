import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api, type ConceptSummary } from '../services/api';
import { Hash, Search } from 'lucide-react';

export default function Concepts() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['concepts', page],
    queryFn: () => api.getConcepts(page, 50),
  });

  const filteredItems = data?.items.filter(
    (c: ConceptSummary) =>
      !search || c.name.toLowerCase().includes(search.toLowerCase())
  ) ?? [];

  return (
    <div className="max-w-4xl mx-auto p-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Concepts</h1>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Filter concepts..."
            className="pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-gray-500">Loading concepts...</div>
      ) : filteredItems.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <Hash className="w-12 h-12 mx-auto mb-3 text-gray-300" />
          <p className="text-lg font-medium text-gray-600">No concepts yet</p>
          <p className="text-sm text-gray-400 mt-1">
            Concepts are automatically extracted when you compile documents.
          </p>
        </div>
      ) : (
        <>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {filteredItems.map((concept: ConceptSummary) => (
              <div
                key={concept.id}
                className="bg-white rounded-lg border border-gray-200 p-4 hover:border-blue-300 transition-colors"
              >
                <div className="flex items-center gap-2 mb-2">
                  <Hash className="w-4 h-4 text-blue-500" />
                  <h3 className="text-sm font-semibold text-gray-900 truncate">
                    {concept.name}
                  </h3>
                </div>
                <div className="flex items-center justify-between text-xs text-gray-500">
                  <span>{concept.mention_count} mention{concept.mention_count !== 1 ? 's' : ''}</span>
                  <span>{new Date(concept.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            ))}
          </div>

          {/* Pagination */}
          {data && data.total > 50 && (
            <div className="flex items-center justify-center gap-4 mt-6">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
              >
                Previous
              </button>
              <span className="text-sm text-gray-600">
                Page {page} of {Math.ceil(data.total / 50)}
              </span>
              <button
                onClick={() => setPage((p) => p + 1)}
                disabled={page * 50 >= data.total}
                className="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
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

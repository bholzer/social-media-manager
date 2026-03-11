import { useState } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router';
import { api } from '@/lib/api';

interface FacebookPage {
  page_id: string;
  name: string;
}

export default function FacebookOAuthCallbackPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const errorParam = searchParams.get('error');
  const pagesParam = searchParams.get('pages');
  const token = searchParams.get('token') ?? '';

  const [connectingPageId, setConnectingPageId] = useState<string | null>(null);
  const [connectError, setConnectError] = useState('');

  // Error state from OAuth callback
  if (errorParam) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="w-full max-w-md rounded-lg bg-white p-8 shadow">
          <h1 className="text-xl font-semibold text-red-600">Connection Failed</h1>
          <p className="mt-2 text-gray-700">{decodeURIComponent(errorParam)}</p>
          <Link
            to="/accounts"
            className="mt-6 inline-block rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            Back to Accounts
          </Link>
        </div>
      </div>
    );
  }

  // Pages selection state
  if (pagesParam) {
    let pages: FacebookPage[] = [];
    try {
      pages = JSON.parse(decodeURIComponent(pagesParam)) as FacebookPage[];
    } catch {
      return (
        <div className="flex min-h-[60vh] items-center justify-center">
          <div className="w-full max-w-md rounded-lg bg-white p-8 shadow">
            <h1 className="text-xl font-semibold text-red-600">Invalid Response</h1>
            <p className="mt-2 text-gray-700">Could not parse pages data from Facebook.</p>
            <Link
              to="/accounts"
              className="mt-6 inline-block rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
            >
              Back to Accounts
            </Link>
          </div>
        </div>
      );
    }

    async function handleSelectPage(page: FacebookPage) {
      setConnectingPageId(page.page_id);
      setConnectError('');
      try {
        await api.post('/oauth/facebook/connect-page', {
          page_id: page.page_id,
          page_name: page.name,
          oauth_user_token: token,
        });
        navigate('/accounts?connected=true', { replace: true });
      } catch (err) {
        setConnectError(err instanceof Error ? err.message : 'Failed to connect page');
        setConnectingPageId(null);
      }
    }

    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="w-full max-w-md rounded-lg bg-white p-8 shadow">
          <h1 className="text-xl font-semibold text-gray-900">Select a Facebook Page</h1>
          <p className="mt-2 text-sm text-gray-600">
            Choose which Facebook Page you want to connect to this account.
          </p>

          {connectError && (
            <div className="mt-4 rounded-md bg-red-50 p-3">
              <p className="text-sm text-red-700">{connectError}</p>
            </div>
          )}

          <ul className="mt-6 space-y-3">
            {pages.map((page) => (
              <li key={page.page_id}>
                <button
                  onClick={() => handleSelectPage(page)}
                  disabled={connectingPageId !== null}
                  className="w-full rounded-lg border border-gray-200 bg-white px-4 py-3 text-left font-medium text-gray-900 transition hover:border-blue-400 hover:bg-blue-50 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {connectingPageId === page.page_id ? (
                    <span className="flex items-center gap-2">
                      <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
                      Connecting...
                    </span>
                  ) : (
                    page.name
                  )}
                </button>
              </li>
            ))}
          </ul>

          <Link
            to="/accounts"
            className="mt-6 inline-block text-sm text-gray-500 hover:text-gray-700"
          >
            Cancel
          </Link>
        </div>
      </div>
    );
  }

  // Fallback: no pages or error param — redirect to accounts
  navigate('/accounts', { replace: true });
  return (
    <div className="flex min-h-[60vh] items-center justify-center">
      <p className="text-gray-500">Redirecting...</p>
    </div>
  );
}

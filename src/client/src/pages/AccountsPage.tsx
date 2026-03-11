import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router';
import { api } from '@/lib/api';

interface SocialAccount {
  id: string;
  user_id: string;
  platform: string;
  platform_user_id: string;
  token_expires_at: string | null;
}

function getAccountStatus(tokenExpiresAt: string | null): 'connected' | 'expired' {
  if (tokenExpiresAt === null) {
    return 'connected';
  }
  if (new Date(tokenExpiresAt) > new Date()) {
    return 'connected';
  }
  return 'expired';
}

export default function AccountsPage() {
  const [accounts, setAccounts] = useState<SocialAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [connectingFacebook, setConnectingFacebook] = useState(false);

  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  function fetchAccounts() {
    setLoading(true);
    api.get<SocialAccount[]>('/social-accounts/')
      .then((data) => {
        setAccounts(data);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'Failed to load accounts');
      })
      .finally(() => {
        setLoading(false);
      });
  }

  useEffect(() => {
    fetchAccounts();
  }, []);

  useEffect(() => {
    const connected = searchParams.get('connected');
    const errorParam = searchParams.get('error');

    if (connected === 'true') {
      setSuccessMessage('Facebook account connected successfully!');
      fetchAccounts();
      navigate('/accounts', { replace: true });
    } else if (errorParam) {
      setError(decodeURIComponent(errorParam));
      navigate('/accounts', { replace: true });
    }
  }, [searchParams, navigate]);

  async function handleDisconnect(accountId: string) {
    if (!window.confirm('Are you sure you want to disconnect this account? This cannot be undone.')) {
      return;
    }
    try {
      await api.delete(`/social-accounts/${accountId}`);
      setAccounts(prev => prev.filter(a => a.id !== accountId));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to disconnect account');
    }
  }

  async function handleConnectFacebook() {
    setConnectingFacebook(true);
    setError('');
    try {
      const data = await api.get<{ url: string }>('/oauth/facebook/connect');
      window.location.href = data.url;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to initiate Facebook connection');
      setConnectingFacebook(false);
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Social Accounts</h1>
          <p className="mt-2 text-gray-600">Manage your connected social media accounts.</p>
        </div>
        <button
          onClick={handleConnectFacebook}
          disabled={connectingFacebook}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {connectingFacebook ? 'Connecting...' : 'Connect Facebook'}
        </button>
      </div>

      {successMessage && (
        <div className="mt-4 rounded-md bg-green-50 p-4">
          <p className="text-sm font-medium text-green-800">{successMessage}</p>
        </div>
      )}

      <div className="mt-6">
        {loading && (
          <p className="text-gray-500">Loading accounts...</p>
        )}

        {!loading && error && (
          <p className="text-red-600">{error}</p>
        )}

        {!loading && !error && accounts.length === 0 && (
          <div className="rounded-lg border-2 border-dashed border-gray-300 p-10 text-center">
            <h3 className="text-lg font-medium text-gray-900">No connected accounts</h3>
            <p className="mt-2 text-sm text-gray-500">
              Connect a social media account to start publishing.
            </p>
          </div>
        )}

        {!loading && !error && accounts.length > 0 && (
          <ul className="space-y-4">
            {accounts.map((account) => {
              const status = getAccountStatus(account.token_expires_at);
              return (
                <li
                  key={account.id}
                  className="flex items-center justify-between rounded-lg bg-white p-4 shadow"
                >
                  <div>
                    <p className="font-medium capitalize">{account.platform}</p>
                    <p className="text-sm text-gray-500">{account.platform_user_id}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    {status === 'connected' ? (
                      <span className="rounded-full bg-green-100 px-3 py-1 text-sm font-medium text-green-700">
                        Connected
                      </span>
                    ) : (
                      <span className="rounded-full bg-red-100 px-3 py-1 text-sm font-medium text-red-700">
                        Expired
                      </span>
                    )}
                    <button
                      onClick={() => handleDisconnect(account.id)}
                      className="text-sm text-red-600 hover:text-red-800 hover:underline"
                    >
                      Disconnect
                    </button>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
}

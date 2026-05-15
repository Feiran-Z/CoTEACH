'use client';

import { useState, useRef, useEffect } from 'react';
import { Play, ShieldCheck, Download, Terminal } from 'lucide-react';

export default function Home() {
  const [folder, setFolder] = useState('');
  const [prompt, setPrompt] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [baseUrl, setBaseUrl] = useState('https://api.deepseek.com/anthropic');
  const [model, setModel] = useState('deepseek-v4-flash');

  const [output, setOutput] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const outputRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  const API_URL = process.env.NEXT_PUBLIC_API_URL;

  // Auto-scroll output
  useEffect(() => {
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight;
    }
  }, [output]);

  const handleRun = async () => {
    if (!folder || !prompt || !apiKey) return;
    setIsRunning(true);
    setOutput('');

    const formData = new FormData();
    formData.append('folder', folder);
    formData.append('prompt', prompt);
    formData.append('api_key', apiKey);
    formData.append('base_url', baseUrl);
    formData.append('model', model);

    // Close previous connection if any
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const eventSource = new EventSource(
      `${API_URL}${new URLSearchParams(formData as any).toString()}`
    );
    eventSourceRef.current = eventSource;

    eventSource.onmessage = (event) => {
      const text = event.data;
      setOutput((prev) => prev + text + '\n');
      if (text.includes('[DONE]') || text.includes('[ERROR]')) {
        eventSource.close();
        setIsRunning(false);
      }
    };

    eventSource.onerror = () => {
      setOutput((prev) => prev + '\n--- Connection closed or error ---\n');
      eventSource.close();
      setIsRunning(false);
    };
  };

  const handleStop = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      setIsRunning(false);
      setOutput((prev) => prev + '\n[STOPPED BY USER]\n');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <aside className="w-96 bg-white border-r border-gray-200 p-6 flex flex-col space-y-6">
        <div className="flex items-center space-x-2">
          <Terminal className="h-6 w-6 text-blue-600" />
          <h1 className="text-xl font-bold text-gray-900">Coteach Agent</h1>
        </div>

        {/* Folder path */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Project Folder Path</label>
          <input
            type="text"
            value={folder}
            onChange={(e) => setFolder(e.target.value)}
            placeholder="/home/user/project"
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Prompt */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Prompt</label>
          <textarea
            rows={5}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Describe what the agent should do..."
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* API credentials */}
        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">API Key</label>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="sk-ant-..."
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Base URL</label>
            <input
              type="text"
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Model</label>
            <input
              type="text"
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex space-x-3">
          <button
            onClick={handleRun}
            disabled={isRunning}
            className="flex-1 flex items-center justify-center space-x-2 bg-blue-600 text-white font-medium py-2 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition"
          >
            <Play className="h-4 w-4" />
            <span>Run</span>
          </button>
          {isRunning && (
            <button
              onClick={handleStop}
              className="flex-1 flex items-center justify-center space-x-2 bg-red-600 text-white font-medium py-2 px-4 rounded-lg hover:bg-red-700 transition"
            >
              Stop
            </button>
          )}
        </div>

        {/* Verify & Install Section */}
        <div className="border-t pt-4">
          <h2 className="text-sm font-semibold text-gray-700 mb-2">Environment Check</h2>
          <div className="flex space-x-2">
            <VerifyButton />
            <InstallButton />
          </div>
        </div>
      </aside>

      {/* Main Output Area */}
      <main className="flex-1 flex flex-col p-6">
        <div className="flex items-center space-x-2 mb-3">
          <Terminal className="h-5 w-5 text-gray-500" />
          <h2 className="text-lg font-semibold text-gray-800">Agent Output</h2>
        </div>
        <div
          ref={outputRef}
          className="flex-1 bg-gray-900 text-green-400 font-mono text-sm p-4 rounded-lg overflow-y-auto whitespace-pre-wrap"
        >
          {output || 'Waiting for agent to start...'}
        </div>
      </main>
    </div>
  );
}

// ---------- Sub-components (can be in same file or separate) ----------
function VerifyButton() {
  const [status, setStatus] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleVerify = async () => {
    setLoading(true);
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL
      const res = await fetch(`${API_URL}/verify`);
      const data = await res.json();
      const parts = [];
      if (data.mcps_not_installed?.length) parts.push(`MCP missing: ${data.mcps_not_installed.join(', ')}`);
      if (data.mcps_not_connected?.length) parts.push(`MCP disconnected: ${data.mcps_not_connected.join(', ')}`);
      if (data.skills_missing?.length) parts.push(`Skills missing: ${data.skills_missing.join(', ')}`);
      setStatus(parts.length ? parts.join(' | ') : 'All systems ready ✅');
    } catch (e) {
      setStatus('Verification failed');
    }
    setLoading(false);
  };

  return (
    <button
      onClick={handleVerify}
      disabled={loading}
      className="flex items-center space-x-1 bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium py-1.5 px-3 rounded-lg text-sm transition"
    >
      <ShieldCheck className="h-4 w-4" />
      <span>{loading ? 'Checking...' : 'Verify'}</span>
      {status && <span className="text-xs text-gray-500 ml-1 truncate max-w-[150px]">{status}</span>}
    </button>
  );
}

function InstallButton() {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const handleInstall = async () => {
    setLoading(true);
    setMessage('');
    const exaKey = prompt('Enter Exa API key (leave blank to skip Exa installation):');
    const formData = new FormData();
    if (exaKey) {
      formData.append('exa_api_key', exaKey);
      formData.append('install_exa', 'true');
    }
    formData.append('install_skills', '["docx","pptx"]');  // or fetch from verify endpoint

    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL
      const res = await fetch(`${API_URL}/install`, { method: 'POST', body: formData });
      const data = await res.json();
      if (data.errors?.length) {
        setMessage(`Errors: ${data.errors.join(', ')}`);
      } else {
        setMessage('Installation successful ✅');
      }
    } catch (e) {
      setMessage('Installation failed');
    }
    setLoading(false);
  };

  return (
    <button
      onClick={handleInstall}
      disabled={loading}
      className="flex items-center space-x-1 bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium py-1.5 px-3 rounded-lg text-sm transition"
    >
      <Download className="h-4 w-4" />
      <span>{loading ? 'Installing...' : 'Install Missing'}</span>
      {message && <span className="text-xs text-gray-500 ml-1">{message}</span>}
    </button>
  );
}
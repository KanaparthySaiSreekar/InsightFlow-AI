'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { projectsAPI, llmConfigAPI } from '@/lib/api';
import { Project, LLMConfig } from '@/types';
import toast from 'react-hot-toast';

export default function DashboardPage() {
  const router = useRouter();
  const { user, logout } = useAuth();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showLLMModal, setShowLLMModal] = useState(false);
  const [llmConfig, setLlmConfig] = useState<LLMConfig | null>(null);

  // Upload form
  const [projectName, setProjectName] = useState('');
  const [projectDescription, setProjectDescription] = useState('');
  const [file, setFile] = useState<File | null>(null);

  // LLM config form
  const [llmProvider, setLlmProvider] = useState<'openai' | 'google' | 'anthropic'>('openai');
  const [apiKey, setApiKey] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [projectsRes, llmRes] = await Promise.allSettled([
        projectsAPI.getAll(),
        llmConfigAPI.getActive(),
      ]);

      if (projectsRes.status === 'fulfilled') {
        setProjects(projectsRes.value.data);
      }

      if (llmRes.status === 'fulfilled') {
        setLlmConfig(llmRes.value.data);
      }
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!file) {
      toast.error('Please select a file');
      return;
    }

    if (!projectName) {
      toast.error('Please enter a project name');
      return;
    }

    setUploading(true);

    try {
      const formData = new FormData();
      formData.append('name', projectName);
      formData.append('description', projectDescription);
      formData.append('file', file);

      await projectsAPI.create(formData);

      toast.success('Project created successfully!');
      setShowUploadModal(false);
      setProjectName('');
      setProjectDescription('');
      setFile(null);
      loadData();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleLLMConfig = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      await llmConfigAPI.create(llmProvider, apiKey);
      toast.success('LLM configuration saved!');
      setShowLLMModal(false);
      setApiKey('');
      loadData();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to save configuration');
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">InsightFlow AI</h1>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600">{user?.email}</span>
            {!llmConfig && (
              <button
                onClick={() => setShowLLMModal(true)}
                className="rounded-md bg-yellow-500 px-3 py-2 text-sm font-semibold text-white hover:bg-yellow-600"
              >
                Configure LLM
              </button>
            )}
            <button
              onClick={logout}
              className="rounded-md bg-gray-600 px-3 py-2 text-sm font-semibold text-white hover:bg-gray-700"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {/* LLM Warning */}
        {!llmConfig && (
          <div className="mb-6 rounded-md bg-yellow-50 p-4">
            <p className="text-sm text-yellow-800">
              Please configure your LLM API key to enable chat functionality.
            </p>
          </div>
        )}

        {/* Upload Button */}
        <div className="mb-6">
          <button
            onClick={() => setShowUploadModal(true)}
            className="rounded-md bg-primary-600 px-4 py-2 text-sm font-semibold text-white hover:bg-primary-500"
          >
            Upload Data File
          </button>
        </div>

        {/* Projects Grid */}
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {projects.map((project) => (
            <div
              key={project.id}
              className="rounded-lg bg-white p-6 shadow cursor-pointer hover:shadow-lg transition-shadow"
              onClick={() => router.push(`/chat/${project.id}`)}
            >
              <h3 className="text-lg font-semibold text-gray-900">{project.name}</h3>
              {project.description && (
                <p className="mt-2 text-sm text-gray-600">{project.description}</p>
              )}
              <p className="mt-2 text-xs text-gray-500">
                File: {project.original_filename}
              </p>
              <p className="mt-1 text-xs text-gray-400">
                Created: {new Date(project.created_at).toLocaleDateString()}
              </p>
            </div>
          ))}
        </div>

        {projects.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-500">No projects yet. Upload a data file to get started!</p>
          </div>
        )}
      </main>

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="w-full max-w-md rounded-lg bg-white p-6">
            <h2 className="text-xl font-semibold mb-4">Upload Data File</h2>
            <form onSubmit={handleUpload} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Project Name
                </label>
                <input
                  type="text"
                  required
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 px-3 py-2 border"
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Description (optional)
                </label>
                <textarea
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 px-3 py-2 border"
                  rows={3}
                  value={projectDescription}
                  onChange={(e) => setProjectDescription(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Data File (CSV, Excel, JSON)
                </label>
                <input
                  type="file"
                  required
                  accept=".csv,.xlsx,.xls,.json"
                  className="mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                />
              </div>
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowUploadModal(false)}
                  className="rounded-md bg-gray-200 px-4 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={uploading}
                  className="rounded-md bg-primary-600 px-4 py-2 text-sm font-semibold text-white hover:bg-primary-500 disabled:opacity-50"
                >
                  {uploading ? 'Uploading...' : 'Upload'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* LLM Config Modal */}
      {showLLMModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="w-full max-w-md rounded-lg bg-white p-6">
            <h2 className="text-xl font-semibold mb-4">Configure LLM</h2>
            <form onSubmit={handleLLMConfig} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Provider
                </label>
                <select
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 px-3 py-2 border"
                  value={llmProvider}
                  onChange={(e) => setLlmProvider(e.target.value as any)}
                >
                  <option value="openai">OpenAI (GPT-4o)</option>
                  <option value="google">Google (Gemini 1.5 Pro)</option>
                  <option value="anthropic">Anthropic (Claude 3.5 Sonnet)</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  API Key
                </label>
                <input
                  type="password"
                  required
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 px-3 py-2 border"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="sk-..."
                />
              </div>
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowLLMModal(false)}
                  className="rounded-md bg-gray-200 px-4 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="rounded-md bg-primary-600 px-4 py-2 text-sm font-semibold text-white hover:bg-primary-500"
                >
                  Save
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

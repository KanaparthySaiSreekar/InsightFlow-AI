'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { chatAPI, projectsAPI } from '@/lib/api';
import { Chat, Message, Project, ChatQueryResponse } from '@/types';
import DataTable from '@/components/DataTable';
import Chart from '@/components/Chart';
import toast from 'react-hot-toast';

export default function ChatPage() {
  const router = useRouter();
  const params = useParams();
  const projectId = parseInt(params.projectId as string);
  const { user } = useAuth();

  const [project, setProject] = useState<Project | null>(null);
  const [chats, setChats] = useState<Chat[]>([]);
  const [currentChat, setCurrentChat] = useState<Chat | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [queryResponse, setQueryResponse] = useState<ChatQueryResponse | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadProject();
    loadChats();
  }, [projectId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadProject = async () => {
    try {
      const response = await projectsAPI.getById(projectId);
      setProject(response.data);
    } catch (error) {
      toast.error('Failed to load project');
      router.push('/dashboard');
    }
  };

  const loadChats = async () => {
    try {
      const response = await chatAPI.getAll(projectId);
      setChats(response.data);

      if (response.data.length > 0) {
        loadChat(response.data[0].id);
      } else {
        createNewChat();
      }
    } catch (error) {
      console.error('Failed to load chats:', error);
    }
  };

  const loadChat = async (chatId: number) => {
    try {
      const response = await chatAPI.getById(chatId);
      setCurrentChat(response.data);
      setMessages(response.data.messages || []);
    } catch (error) {
      toast.error('Failed to load chat');
    }
  };

  const createNewChat = async () => {
    try {
      const response = await chatAPI.create(projectId, 'New Chat');
      setCurrentChat(response.data);
      setMessages([]);
      setChats([response.data, ...chats]);
    } catch (error) {
      toast.error('Failed to create chat');
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!input.trim() || !currentChat) return;

    const userMessage = input;
    setInput('');
    setLoading(true);

    // Optimistic update
    const tempUserMessage: Message = {
      id: Date.now(),
      role: 'user',
      content: userMessage,
      created_at: new Date().toISOString(),
    };
    setMessages([...messages, tempUserMessage]);

    try {
      const response = await chatAPI.query(currentChat.id, userMessage);
      setQueryResponse(response.data);

      // Add assistant message
      setMessages((prev) => [...prev.slice(0, -1), tempUserMessage, response.data.message]);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to send message');
      setMessages((prev) => prev.slice(0, -1)); // Remove temp message
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <div className="w-64 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <button
            onClick={() => router.push('/dashboard')}
            className="text-sm text-primary-600 hover:text-primary-700 font-medium"
          >
            ← Back to Dashboard
          </button>
          <h2 className="mt-4 text-lg font-semibold text-gray-900 truncate">
            {project?.name}
          </h2>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          <button
            onClick={createNewChat}
            className="w-full mb-4 rounded-md bg-primary-600 px-3 py-2 text-sm font-semibold text-white hover:bg-primary-500"
          >
            New Chat
          </button>

          <div className="space-y-2">
            {chats.map((chat) => (
              <button
                key={chat.id}
                onClick={() => loadChat(chat.id)}
                className={`w-full text-left rounded-md px-3 py-2 text-sm ${
                  currentChat?.id === chat.id
                    ? 'bg-primary-100 text-primary-900'
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                {chat.title}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.map((message, idx) => (
            <div
              key={message.id}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-3xl rounded-lg px-4 py-2 ${
                  message.role === 'user'
                    ? 'bg-primary-600 text-white'
                    : 'bg-white border border-gray-200'
                }`}
              >
                <p className="text-sm">{message.content}</p>

                {message.sql_query && (
                  <details className="mt-2 text-xs opacity-75">
                    <summary className="cursor-pointer">SQL Query</summary>
                    <pre className="mt-1 overflow-x-auto bg-gray-100 text-gray-800 p-2 rounded">
                      {message.sql_query}
                    </pre>
                  </details>
                )}

                {message.error_message && (
                  <p className="mt-2 text-xs text-red-500">{message.error_message}</p>
                )}

                {/* Show data and visualization for the last assistant message */}
                {message.role === 'assistant' &&
                  idx === messages.length - 1 &&
                  queryResponse &&
                  queryResponse.data &&
                  queryResponse.data.length > 0 && (
                    <div className="mt-4 space-y-4">
                      {queryResponse.visualization_type &&
                        queryResponse.visualization_type !== 'table' && (
                          <Chart
                            data={queryResponse.data}
                            type={queryResponse.visualization_type}
                          />
                        )}

                      <DataTable data={queryResponse.data} />
                    </div>
                  )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="bg-white border border-gray-200 rounded-lg px-4 py-2">
                <p className="text-sm text-gray-500">Thinking...</p>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="border-t border-gray-200 bg-white p-4">
          <form onSubmit={handleSendMessage} className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a question about your data..."
              disabled={loading}
              className="flex-1 rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 px-4 py-2 border"
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="rounded-md bg-primary-600 px-6 py-2 text-sm font-semibold text-white hover:bg-primary-500 disabled:opacity-50"
            >
              Send
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

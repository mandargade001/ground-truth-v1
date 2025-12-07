'use client';

import { Sidebar } from '@/components/layout/Sidebar';
import { ChatInterface } from '@/components/feature/chat/ChatInterface';
import { KnowledgeBase } from '@/components/feature/knowledge/KnowledgeBase';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      router.push('/login');
    }
  }, [router]);

  return (
    <div className="flex h-screen w-full bg-background">
      {/* Left Sidebar */}
      <Sidebar />

      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col border-r border-border">
        <ChatInterface />
      </main>

      {/* Right Knowledge Base */}
      <aside className="w-[400px] bg-background p-6 flex flex-col">
        <KnowledgeBase />
      </aside>
    </div>
  );
}

'use client';

import { Button } from '@/components/ui/button';
import { PlusCircle, MessageSquare, Loader2, BarChart } from 'lucide-react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';

interface ChatSession {
    session_id: number;
    message: string;
}

export function Sidebar() {
    const { data: sessions, isLoading } = useQuery({
        queryKey: ['sessions'],
        queryFn: async () => {
            const res = await api.get<ChatSession[]>('/chat/sessions');
            return res.data;
        }
    });

    return (
        <div className="w-64 border-r border-border bg-muted/30 h-full flex flex-col p-4">
            <div className="flex items-center gap-2 px-2 mb-6">
                <div className="h-8 w-8 bg-primary rounded-lg flex items-center justify-center text-primary-foreground font-bold">G</div>
                <h1 className="font-bold text-xl text-foreground">GroundTruth</h1>
            </div>

            <Button className="w-full mb-6 font-semibold shadow-sm" size="lg">
                <PlusCircle className="mr-2 h-4 w-4" />
                New Conversation
            </Button>

            <div className="flex-1 overflow-auto">
                <h2 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3 px-2">History</h2>
                <div className="space-y-1">
                    {isLoading && <div className="flex justify-center p-4"><Loader2 className="h-4 w-4 animate-spin text-muted-foreground" /></div>}

                    {sessions?.map(session => (
                        <Button key={session.session_id} variant="ghost" className="w-full justify-start text-sm font-normal text-muted-foreground hover:bg-muted/50 hover:text-foreground truncate">
                            <MessageSquare className="mr-2 h-4 w-4 opacity-70 shrink-0" />
                            <span className="truncate">{session.message}</span>
                        </Button>
                    ))}

                    {!isLoading && sessions?.length === 0 && (
                        <div className="px-2 text-xs text-muted-foreground">No history yet.</div>
                    )}
                </div>
            </div>

            <div className="border-t border-border pt-4 mt-auto space-y-2">
                <Link href="/dashboard" className="w-full">
                    <Button variant="ghost" className="w-full justify-start text-xs font-semibold text-muted-foreground uppercase tracking-wider hover:bg-muted/50 hover:text-foreground">
                        <BarChart className="mr-2 h-4 w-4" />
                        Dashboard
                    </Button>
                </Link>
                <div className="text-xs text-muted-foreground px-2 pt-2">
                    {sessions?.length || 0} conversations
                </div>
            </div>
        </div>
    );
}

'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, User as UserIcon, Bot, Loader2, Mic, MicOff, Download, Trash, StopCircle, LogOut } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ScrollArea } from '@/components/ui/scroll-area';
import { Textarea } from '@/components/ui/textarea';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { useMutation } from '@tanstack/react-query';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { toast } from 'sonner';

interface Message {
    role: 'user' | 'assistant';
    content: string;
    sources?: string[];
}

export function ChatInterface() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [isListening, setIsListening] = useState(false);
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const audioChunksRef = useRef<Blob[]>([]);
    const scrollRef = useRef<HTMLDivElement>(null);
    const abortControllerRef = useRef<AbortController | null>(null);

    // Auto-scroll
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [messages]);

    // Voice Input Logic (MediaRecorder + Whisper API)
    const startListening = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const mediaRecorder = new MediaRecorder(stream);
            mediaRecorderRef.current = mediaRecorder;
            audioChunksRef.current = [];

            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    audioChunksRef.current.push(event.data);
                }
            };

            mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
                const formData = new FormData();
                formData.append('file', audioBlob, 'recording.webm');

                setIsLoading(true); // Re-use loading state or add specific one if needed
                try {
                    const token = localStorage.getItem('access_token');
                    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
                    const response = await fetch(`${API_BASE_URL}/audio/transcribe`, {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${token}`
                        },
                        body: formData
                    });

                    if (!response.ok) throw new Error('Transcription failed');

                    const data = await response.json();
                    if (data.text) {
                        setInput(prev => prev + (prev ? ' ' : '') + data.text);
                    }
                } catch (error) {
                    console.error("Transcription error:", error);
                    toast.error("Failed to transcribe audio.");
                } finally {
                    setIsLoading(false);
                    // Stop all tracks
                    stream.getTracks().forEach(track => track.stop());
                }
            };

            mediaRecorder.start();
            setIsListening(true);
        } catch (err: any) {
            console.error("Microphone denied:", err);
            toast.error("Microphone access denied or not supported.");
        }
    };

    const stopListening = () => {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
            mediaRecorderRef.current.stop();
            setIsListening(false);
        }
    };

    const handleStop = () => {
        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
            abortControllerRef.current = null;
            setIsLoading(false);
            toast.info("Generation stopped.");
        }
    };

    const handleClear = () => {
        if (confirm("Clear chat history?")) {
            setMessages([]);
            toast.info("Chat cleared.");
        }
    };

    const handleLogout = () => {
        if (confirm("Are you sure you want to log out?")) {
            localStorage.removeItem('access_token');
            window.location.href = '/login';
        }
    };

    const handleDownload = () => {
        const data = JSON.stringify(messages, null, 2);
        const blob = new Blob([data], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `chat-history-${new Date().toISOString()}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        toast.success("Chat history downloaded.");
    };

    // Custom Stream Handler for Raw Text
    const handleSendRaw = async () => {
        if (!input.trim() || isLoading) return;

        const userMsg = input.trim();
        setInput('');
        setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
        setIsLoading(true);

        // Placeholder for bot
        setMessages(prev => [...prev, { role: 'assistant', content: '' }]);

        abortControllerRef.current = new AbortController();

        try {
            const token = localStorage.getItem('access_token');
            const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
            const response = await fetch(`${API_BASE_URL}/chat/message`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ message: userMsg }),
                signal: abortControllerRef.current.signal
            });

            if (!response.body) return;
            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            let buffer = "";
            let hasReceivedMetadata = false;

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                const chunk = decoder.decode(value, { stream: true });

                if (!hasReceivedMetadata) {
                    buffer += chunk;
                    // Check for metadata boundary
                    const splitIdx = buffer.indexOf('\n\n');
                    if (splitIdx !== -1) {
                        const jsonStr = buffer.substring(0, splitIdx);
                        try {
                            const data = JSON.parse(jsonStr);
                            if (data.type === 'sources') {
                                setMessages(prev => {
                                    const newMsgs = [...prev];
                                    const lastMsg = newMsgs[newMsgs.length - 1];
                                    if (lastMsg.role === 'assistant') {
                                        return [...newMsgs.slice(0, -1), { ...lastMsg, sources: data.data }];
                                    }
                                    return prev;
                                });
                            }
                            hasReceivedMetadata = true;
                            // Process remaining part of buffer as text
                            const remaining = buffer.substring(splitIdx + 2);
                            if (remaining) {
                                setMessages(prev => {
                                    const newMsgs = [...prev];
                                    const lastMsg = newMsgs[newMsgs.length - 1];
                                    if (lastMsg.role === 'assistant') {
                                        return [...newMsgs.slice(0, -1), { ...lastMsg, content: lastMsg.content + remaining }];
                                    }
                                    return prev;
                                });
                            }
                        } catch (e) {
                            console.error("JSON Parse error", e);
                            // If parse fails, assume it's just text? Or keep buffering? 
                            // For now assuming broken JSON means we skip it or treat as text if it doesn't look like JSON
                            hasReceivedMetadata = true; // Stop trying to parse JSON
                        }
                        buffer = ""; // Clear buffer
                    }
                    // Else keep buffering until we find \n\n
                } else {
                    // Metadata already received, just stream text
                    setMessages(prev => {
                        const newMsgs = [...prev];
                        const lastMsg = newMsgs[newMsgs.length - 1];
                        if (lastMsg.role === 'assistant') {
                            return [...newMsgs.slice(0, -1), { ...lastMsg, content: lastMsg.content + chunk }];
                        }
                        return prev;
                    });
                }
            }
        } catch (err: any) {
            if (err.name === 'AbortError') {
                console.log("Stream aborted");
            } else {
                console.error("Chat error", err);
                toast.error("Failed to send message.");
            }
        } finally {
            setIsLoading(false);
            abortControllerRef.current = null;
        }
    }


    return (
        <div className="flex flex-col h-full bg-white relative">
            {/* Header */}
            <div className="border-b border-border p-4 flex items-center justify-between bg-white/80 backdrop-blur z-10">
                <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-muted-foreground">Knowledge Base AI Assistant</span>
                    {isLoading && <Loader2 className="h-3 w-3 animate-spin text-muted-foreground" />}
                </div>
                <div className="flex items-center gap-2">
                    <Button variant="ghost" size="icon" onClick={handleDownload} title="Export Chat">
                        <Download className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="icon" onClick={handleClear} title="Clear Chat" className="text-destructive hover:bg-destructive/10">
                        <Trash className="h-4 w-4" />
                    </Button>
                    <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                            <Button variant="ghost" className="relative h-8 w-8 rounded-full">
                                <Avatar className="h-8 w-8">
                                    <AvatarFallback className="bg-primary text-white text-xs cursor-pointer">A</AvatarFallback>
                                </Avatar>
                            </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent className="w-56" align="end" forceMount>
                            <DropdownMenuLabel className="font-normal">
                                <div className="flex flex-col space-y-1">
                                    <p className="text-sm font-medium leading-none">User</p>
                                    <p className="text-xs leading-none text-muted-foreground">
                                        user@example.com
                                    </p>
                                </div>
                            </DropdownMenuLabel>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem onClick={handleLogout} className="text-destructive cursor-pointer">
                                <LogOut className="mr-2 h-4 w-4" />
                                <span>Log out</span>
                            </DropdownMenuItem>
                        </DropdownMenuContent>
                    </DropdownMenu>
                </div>
            </div>

            {/* Messages */}
            <ScrollArea className="flex-1 p-6">
                <div className="max-w-3xl mx-auto space-y-6 pb-4">
                    {messages.length === 0 && (
                        <div className="flex flex-col items-center justify-center h-[50vh] text-center opacity-50">
                            <div className="h-16 w-16 bg-primary/10 rounded-2xl flex items-center justify-center mb-4 text-primary font-bold text-2xl">G</div>
                            <h3 className="text-lg font-semibold">Hello! I'm GroundTruth.</h3>
                            <p className="text-sm text-muted-foreground max-w-sm">
                                Upload documents or paste text to build your knowledge base, then ask me questions!
                            </p>
                        </div>
                    )}

                    {messages.map((msg, idx) => (
                        <div key={idx} className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                            {msg.role === 'assistant' && (
                                <Avatar className="h-8 w-8 mt-1">
                                    <AvatarFallback className="bg-primary text-white text-xs">G</AvatarFallback>
                                </Avatar>
                            )}
                            <div className={`
                                max-w-[80%] rounded-2xl px-4 py-3 text-sm overflow-hidden
                                ${msg.role === 'user'
                                    ? 'bg-secondary text-secondary-foreground rounded-tr-none'
                                    : 'bg-background border border-border shadow-sm rounded-tl-none'}
                            `}>
                                <div className="leading-relaxed whitespace-pre-wrap markdown-body">
                                    {/* Markdown Rendering */}
                                    {msg.role === 'assistant' ? (
                                        <ReactMarkdown
                                            remarkPlugins={[remarkGfm]}
                                            components={{
                                                code({ node, inline, className, children, ...props }: any) {
                                                    const match = /language-(\w+)/.exec(className || '')
                                                    return !inline && match ? (
                                                        <div className="rounded-md overflow-hidden my-2 border border-border/50">
                                                            <div className="bg-muted px-3 py-1 text-xs text-muted-foreground border-b border-border/50 flex justify-between">
                                                                <span>{match[1]}</span>
                                                            </div>
                                                            <div className="p-3 bg-muted/30 overflow-x-auto">
                                                                <code className={className} {...props}>
                                                                    {children}
                                                                </code>
                                                            </div>
                                                        </div>
                                                    ) : (
                                                        <code className="bg-muted px-1.5 py-0.5 rounded text-xs font-mono" {...props}>
                                                            {children}
                                                        </code>
                                                    )
                                                }
                                            }}
                                        >
                                            {msg.content}
                                        </ReactMarkdown>
                                    ) : (
                                        msg.content
                                    )}
                                </div>
                                {msg.sources && msg.sources.length > 0 && (
                                    <div className="mt-3 pt-3 border-t border-border/50">
                                        <p className="text-xs font-semibold text-muted-foreground mb-1">Sources:</p>
                                        <div className="flex flex-wrap gap-1">
                                            {msg.sources.map((src, i) => (
                                                <span key={i} className="text-[10px] bg-muted px-1.5 py-0.5 rounded text-muted-foreground border border-border">
                                                    {src}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                            {msg.role === 'user' && (
                                <Avatar className="h-8 w-8 mt-1">
                                    <AvatarFallback>U</AvatarFallback>
                                </Avatar>
                            )}
                        </div>
                    ))}
                    {isLoading && messages[messages.length - 1]?.role !== 'assistant' && (
                        <div className="flex gap-4 justify-start">
                            <Avatar className="h-8 w-8 mt-1">
                                <AvatarFallback>G</AvatarFallback>
                            </Avatar>
                            <div className="bg-background border border-border shadow-sm rounded-2xl rounded-tl-none px-4 py-3">
                                <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                            </div>
                        </div>
                    )}
                    <div ref={scrollRef} />
                </div>
            </ScrollArea>

            {/* Input Area */}
            <div className="p-4 border-t border-border">
                <div className="max-w-3xl mx-auto relative cursor-text">
                    <Textarea
                        placeholder="Ask a question..."
                        className="min-h-[60px] pl-10 pr-24 resize-none shadow-sm rounded-xl py-4 border-muted-foreground/20 focus-visible:ring-primary"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                                e.preventDefault();
                                handleSendRaw();
                            }
                        }}
                    />

                    {/* Voice Button */}
                    <div className="absolute left-3 bottom-0 h-full flex items-center">
                        <div
                            onClick={isListening ? stopListening : startListening}
                            className={`cursor-pointer p-1.5 rounded-full transition-colors ${isListening ? 'bg-red-100 text-red-500 animate-pulse' : 'text-muted-foreground hover:bg-muted'}`}
                        >
                            {isListening ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
                        </div>
                    </div>

                    <div className="absolute right-3 bottom-3 flex items-center gap-2">
                        {isLoading ? (
                            <Button
                                size="icon"
                                className="h-8 w-8 bg-destructive hover:bg-destructive/90"
                                onClick={handleStop}
                            >
                                <StopCircle className="h-4 w-4 text-white" />
                            </Button>
                        ) : (
                            <Button
                                size="icon"
                                className="h-8 w-8 bg-[#D4A353] hover:bg-[#C29345]"
                                onClick={handleSendRaw}
                                disabled={!input.trim()}
                            >
                                <Send className="h-4 w-4 text-white" />
                            </Button>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

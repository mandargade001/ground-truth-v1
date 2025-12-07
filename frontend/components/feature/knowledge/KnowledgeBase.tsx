'use client';

import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { UploadCloud, FileText, Trash2, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { UploadedFile } from '@/types';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Input } from '@/components/ui/input';

import { toast } from 'sonner';

import { Dialog, DialogContent, DialogTrigger } from '@/components/ui/dialog';
import { Eye } from 'lucide-react';

export function KnowledgeBase() {
    const queryClient = useQueryClient();
    const [uploading, setUploading] = useState(false);
    const [previewUrl, setPreviewUrl] = useState<string | null>(null);
    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL?.replace('/api/v1', '') || 'http://localhost:8000'; // Base for static files matches backend root

    // Fetch Files
    const { data: files, isLoading } = useQuery({
        queryKey: ['files'],
        queryFn: async () => {
            const res = await api.get<any[]>('/documents/');
            return res.data;
        },
        initialData: [],
        refetchInterval: 5000 // Poll every 5s to check for processing status
    });

    // Upload Mutation
    const uploadMutation = useMutation({
        mutationFn: async (file: File) => {
            const formData = new FormData();
            formData.append('file', file);
            await api.post('/documents/upload', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
        },
        onMutate: () => {
            setUploading(true);
            toast.info("Starting upload...");
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['files'] });
            toast.success("Document uploaded successfully. Processing started.");
            setUploading(false);
        },
        onError: () => {
            toast.error("Upload failed. Please try again.");
            setUploading(false);
        }
    });

    // Delete Mutation
    const deleteMutation = useMutation({
        mutationFn: async (id: number) => {
            await api.delete(`/documents/${id}`);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['files'] });
            toast.success("Document deleted.");
        },
        onError: () => {
            toast.error("Delete failed.");
        }
    });

    // Dropzone
    const onDrop = useCallback((acceptedFiles: File[]) => {
        acceptedFiles.forEach(file => {
            uploadMutation.mutate(file);
        });
    }, [uploadMutation]);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop });

    // Status Icon Helper
    const StatusIcon = ({ status }: { status: string }) => {
        switch (status) {
            case 'pending': return <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />;
            case 'processing': return <Loader2 className="h-4 w-4 animate-spin text-primary" />;
            case 'indexed': return <CheckCircle className="h-4 w-4 text-green-500" />;
            case 'failed': return <AlertCircle className="h-4 w-4 text-destructive" />;
            default: return <FileText className="h-4 w-4" />;
        }
    };

    return (
        <div className="flex flex-col h-full">


            {/* Upload Area */}
            <div
                {...getRootProps()}
                className={`
                    border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors mb-6
                    ${isDragActive ? 'border-primary bg-primary/5' : 'border-border hover:border-primary/50'}
                `}
            >
                <input {...getInputProps()} />
                <div className="flex flex-col items-center justify-center gap-2">
                    <UploadCloud className="h-8 w-8 text-muted-foreground" />
                    <p className="text-sm font-medium text-foreground">Drag files here or click to upload</p>
                    <p className="text-xs text-muted-foreground">PDF, TXT, DOC, Markdown</p>
                </div>
            </div>

            <div className="mb-6">
                <p className="text-sm font-medium mb-2">Or paste text directly</p>
                <Input placeholder="Paste your text content here..." className="mb-2" />
                <Button variant="outline" className="w-full">Add Text to Knowledge Base</Button>
            </div>

            {/* File List */}
            <div className="flex-1 flex flex-col min-h-0">
                <h3 className="font-semibold text-sm mb-3">Knowledge Base</h3>
                <ScrollArea className="flex-1 -mx-4 px-4">
                    <div className="space-y-3">
                        {files.map(file => (
                            <Card key={file.id} className="shadow-sm border-border group">
                                <CardContent className="p-3 flex items-center gap-3">
                                    <div><StatusIcon status={file.status} /></div>
                                    <div className="flex-1 min-w-0">
                                        <p className="text-sm font-medium truncate">{file.filename}</p>
                                        <p className="text-xs text-muted-foreground">
                                            {/* {(file.size / 1024).toFixed(2)} KB */}
                                            {new Date(file.created_at).toLocaleDateString()}
                                        </p>
                                    </div>
                                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                        <Dialog>
                                            <DialogTrigger asChild>
                                                <Button size="icon" variant="ghost" className="h-8 w-8 text-muted-foreground hover:text-foreground"
                                                    onClick={() => setPreviewUrl(`${API_BASE_URL}${file.preview_url}`)}
                                                >
                                                    <Eye className="h-4 w-4" />
                                                </Button>
                                            </DialogTrigger>
                                            <DialogContent className="max-w-4xl h-[80vh]">
                                                {file.filename.endsWith('.pdf') ? (
                                                    <iframe src={`${API_BASE_URL}${file.preview_url}`} className="w-full h-full rounded border-none" />
                                                ) : (
                                                    <div className="w-full h-full flex items-center justify-center text-muted-foreground">
                                                        Preview only available for PDF currently. <br />
                                                        <a href={`${API_BASE_URL}${file.preview_url}`} target="_blank" className="text-primary underline ml-1">Download</a>
                                                    </div>
                                                )}
                                            </DialogContent>
                                        </Dialog>

                                        <Button size="icon" variant="ghost" className="h-8 w-8 text-destructive hover:bg-destructive/10"
                                            onClick={() => {
                                                if (confirm('Are you sure you want to delete this document?')) {
                                                    deleteMutation.mutate(file.id);
                                                }
                                            }}
                                        >
                                            <Trash2 className="h-4 w-4" />
                                        </Button>
                                    </div>
                                </CardContent>
                            </Card>
                        ))}
                        {files.length === 0 && !isLoading && (
                            <div className="text-center text-xs text-muted-foreground py-4">
                                No documents added yet.
                            </div>
                        )}
                        {isLoading && (
                            <div className="text-center text-xs text-muted-foreground py-4">
                                Loading...
                            </div>
                        )}
                    </div>
                </ScrollArea>
            </div>
        </div>
    );
}

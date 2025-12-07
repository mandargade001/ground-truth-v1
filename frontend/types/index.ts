export interface UploadedFile {
    id: number;
    filename: string;
    status: 'pending' | 'processing' | 'indexed' | 'failed';
    created_at: string;
}

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Send, Loader2 } from 'lucide-react';
import { Alert, AlertDescription } from "@/components/ui/alert";

interface QuestionFormProps {
  topicId: string;
  onSubmit: (response: any) => void;
}

export function QuestionForm({ topicId, onSubmit }: QuestionFormProps) {
  const [question, setQuestion] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!question.trim()) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/v1/topics/${topicId}/responses`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      });

      if (!response.ok) {
        throw new Error('Failed to submit question');
      }

      const data = await response.json();
      onSubmit(data);
      setQuestion('');
    } catch (error) {
      setError('Failed to submit question. Please try again.');
      console.error('Error submitting question:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card className="w-full border border-primary/20 bg-card/80 backdrop-blur">
      <CardHeader>
        <CardTitle className="font-mono flex items-center gap-2">
          <span className="text-primary/80">&gt;</span> Ask a Question
        </CardTitle>
        <CardDescription className="font-mono flex items-center gap-2">
          <span className="text-primary/60">$</span> Ask your question and our AI agents will provide their perspectives.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        
        <div className="space-y-4">
          <Textarea
            placeholder="Type your question here..."
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            className="min-h-[120px] resize-none"
            disabled={isLoading}
          />
          <Button
            onClick={handleSubmit}
            disabled={isLoading || !question.trim()}
            className="w-full"
          >
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Asking AI Agents...
              </>
            ) : (
              <>
                <Send className="mr-2 h-4 w-4" />
                Submit Question
              </>
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

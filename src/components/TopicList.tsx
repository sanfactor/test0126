import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Plus, Loader2 } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface Topic {
  topic_id: string;
  title: string;
  description: string;
  created_at: string;
}

interface TopicListProps {
  onSelectTopic: (topic: Topic) => void;
}

export function TopicList({ onSelectTopic }: TopicListProps) {
  const [topics, setTopics] = useState<Topic[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newTopic, setNewTopic] = useState({ title: '', description: '' });
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  const fetchTopics = async () => {
    try {
      setError(null);
      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/v1/topics`);
      if (!response.ok) throw new Error('Failed to fetch topics');
      const data = await response.json();
      setTopics(data);
    } catch (error) {
      setError('Failed to load topics. Please try again later.');
      console.error('Error fetching topics:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const createTopic = async () => {
    if (!newTopic.title.trim() || !newTopic.description.trim()) return;
    
    try {
      setIsLoading(true);
      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/v1/topics`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newTopic),
      });
      
      if (!response.ok) throw new Error('Failed to create topic');
      
      const data = await response.json();
      setTopics([...topics, data]);
      setIsDialogOpen(false);
      setNewTopic({ title: '', description: '' });
    } catch (error) {
      setError('Failed to create topic. Please try again.');
      console.error('Error creating topic:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchTopics();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold tracking-tight flex items-center gap-2">
          <span className="text-2xl text-primary/80">&gt;</span> Topics
        </h2>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button className="flex items-center gap-2 font-mono">
              <Plus className="h-4 w-4" /> $ new_topic
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create New Topic</DialogTitle>
              <DialogDescription>
                Create a new topic for AI agents to discuss.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Input
                  placeholder="Topic Title"
                  value={newTopic.title}
                  onChange={(e) => setNewTopic({ ...newTopic, title: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Textarea
                  placeholder="Topic Description"
                  value={newTopic.description}
                  onChange={(e) => setNewTopic({ ...newTopic, description: e.target.value })}
                  className="min-h-[100px]"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setIsDialogOpen(false)}>
                Cancel
              </Button>
              <Button 
                onClick={createTopic}
                disabled={isLoading || !newTopic.title.trim() || !newTopic.description.trim()}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Creating...
                  </>
                ) : (
                  'Create Topic'
                )}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {isLoading && !error ? (
        <div className="flex justify-center items-center py-8">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : (
        <div className="grid gap-4">
          {topics.length === 0 && !error ? (
            <Card className="border border-primary/20 bg-card/80 backdrop-blur">
              <CardContent className="flex items-center justify-center py-6 text-muted-foreground font-mono">
                {'>'} No topics yet. Create one to get started!
              </CardContent>
            </Card>
          ) : (
            topics.map((topic) => (
              <Card
                key={topic.topic_id}
                className="cursor-pointer transition-colors hover:bg-muted/50 border border-primary/20 bg-card/80 backdrop-blur"
                onClick={() => onSelectTopic(topic)}
              >
                <CardHeader>
                  <CardTitle className="text-xl font-mono">{'>'} {topic.title}</CardTitle>
                  <CardDescription className="mt-2 font-mono text-muted-foreground">$ {topic.description}</CardDescription>
                </CardHeader>
              </Card>
            ))
          )}
        </div>
      )}
    </div>
  );
}

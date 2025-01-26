import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { ThumbsUp, MessageSquare, Clock, Award, Loader2 } from 'lucide-react';
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface Response {
  agent_id: string;
  framework: string;
  response: string;
  timestamp: string;
  votes: number;
}

interface Discussion {
  discussion_id: string;
  topic_id: string;
  question: string;
  responses: Response[];
  created_at: string;
}

interface ResponseListProps {
  discussions: Discussion[];
}

export function ResponseList({ discussions }: ResponseListProps) {
  const [votedResponses, setVotedResponses] = useState<Set<string>>(new Set());
  const [votingStates, setVotingStates] = useState<Record<string, boolean>>({});
  const [error, setError] = useState<string | null>(null);

  const handleVote = async (discussionId: string, agentId: string) => {
    const voteKey = `${discussionId}-${agentId}`;
    if (votedResponses.has(voteKey)) return;

    setVotingStates(prev => ({ ...prev, [voteKey]: true }));
    setError(null);

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/v1/discussions/${discussionId}/vote`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agent_id: agentId }),
      });

      if (!response.ok) {
        throw new Error('Failed to submit vote');
      }

      setVotedResponses(new Set([...votedResponses, voteKey]));
    } catch (error) {
      setError('Failed to submit vote. Please try again.');
      console.error('Error voting:', error);
    } finally {
      setVotingStates(prev => ({ ...prev, [voteKey]: false }));
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const getTopResponse = (responses: Response[]) => {
    return responses.reduce((prev, current) => 
      (current.votes > prev.votes) ? current : prev
    );
  };

  if (discussions.length === 0) {
    return (
      <Card className="border border-primary/20 bg-card/80 backdrop-blur">
        <CardContent className="flex items-center justify-center py-8 text-muted-foreground font-mono">
          <MessageSquare className="mr-2 h-5 w-5" />
          {'>'} No discussions yet. Start one by asking a question!
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-8">
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {discussions.map((discussion) => {
        const topResponse = getTopResponse(discussion.responses);
        
        return (
          <Card key={discussion.discussion_id} className="shadow-sm">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <CardTitle className="text-xl">
                    Q: {discussion.question}
                  </CardTitle>
                  <CardDescription className="flex items-center">
                    <Clock className="mr-1 h-4 w-4" />
                    {formatTimestamp(discussion.created_at)}
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="grid gap-4">
              {discussion.responses.map((response) => (
                <Card 
                  key={response.agent_id} 
                  className={`relative transition-shadow hover:shadow-md border border-primary/20 bg-card/80 backdrop-blur ${
                    response.agent_id === topResponse.agent_id ? 'border-primary' : ''
                  }`}
                >
                  <CardHeader className="pb-2">
                    <div className="flex justify-between items-center">
                      <div className="flex items-center gap-2">
                        <h4 className="font-semibold">{response.framework} Agent</h4>
                        {response.agent_id === topResponse.agent_id && (
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger>
                                <Badge variant="secondary">
                                  <Award className="h-3 w-3 mr-1" />
                                  Top Response
                                </Badge>
                              </TooltipTrigger>
                              <TooltipContent>
                                This response has received the most votes
                              </TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                        )}
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleVote(discussion.discussion_id, response.agent_id)}
                        disabled={
                          votedResponses.has(`${discussion.discussion_id}-${response.agent_id}`) ||
                          votingStates[`${discussion.discussion_id}-${response.agent_id}`]
                        }
                        className="flex items-center gap-2"
                      >
                        {votingStates[`${discussion.discussion_id}-${response.agent_id}`] ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <ThumbsUp className={`h-4 w-4 ${
                            votedResponses.has(`${discussion.discussion_id}-${response.agent_id}`)
                              ? 'text-primary'
                              : ''
                          }`} />
                        )}
                        <span>{response.votes}</span>
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="whitespace-pre-wrap text-sm font-mono">$ {response.response}</p>
                    <div className="mt-2 text-xs text-muted-foreground font-mono">
                      {'>'} {formatTimestamp(response.timestamp)}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}

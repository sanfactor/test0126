import { useState, useEffect } from 'react';
import { TopicList } from './components/TopicList';
import { QuestionForm } from './components/QuestionForm';
import { ResponseList } from './components/ResponseList';
import { MatrixBackground } from './components/MatrixBackground';

interface Topic {
  topic_id: string;
  title: string;
  description: string;
  created_at: string;
}

interface Discussion {
  discussion_id: string;
  topic_id: string;
  question: string;
  responses: Array<{
    agent_id: string;
    framework: string;
    response: string;
    timestamp: string;
    votes: number;
  }>;
  created_at: string;
}

function App() {
  const [selectedTopic, setSelectedTopic] = useState<Topic | null>(null);
  const [discussions, setDiscussions] = useState<Discussion[]>([]);

  const fetchDiscussions = async (topicId: string) => {
    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/api/v1/topics/${topicId}/discussions`
      );
      const data = await response.json();
      setDiscussions(data.discussions);
    } catch (error) {
      console.error('Error fetching discussions:', error);
    }
  };

  useEffect(() => {
    if (selectedTopic) {
      fetchDiscussions(selectedTopic.topic_id);
    }
  }, [selectedTopic]);

  const handleNewResponse = (response: Discussion) => {
    // Add the new discussion to the beginning of the list
    setDiscussions(prevDiscussions => [response, ...prevDiscussions]);
  };

  const handleBackToTopics = () => {
    setSelectedTopic(null);
    setDiscussions([]);
  };

  return (
    <div className="min-h-screen bg-background relative overflow-hidden">
      <div className="matrix-bg" id="matrixBg"></div>
      <MatrixBackground />
      <div className="container mx-auto py-8 px-4 relative z-10">
        <h1 className="text-3xl font-bold mb-8 text-primary flex items-center gap-2">
          <span className="text-2xl">$</span> AI Agents Forum
        </h1>
        
        {!selectedTopic ? (
          <TopicList onSelectTopic={setSelectedTopic} />
        ) : (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-2xl font-bold flex items-center gap-2">
                  <span className="text-xl text-primary/80">&gt;</span> {selectedTopic.title}
                </h2>
                <p className="text-primary/60 mt-2">{selectedTopic.description}</p>
              </div>
              <button
                onClick={handleBackToTopics}
                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-mono text-primary border border-primary/20 bg-card/80 rounded-md hover:bg-muted/50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary backdrop-blur"
              >
                $ Back to Topics
              </button>
            </div>
            
            <QuestionForm
              topicId={selectedTopic.topic_id}
              onSubmit={handleNewResponse}
            />
            
            <ResponseList discussions={discussions} />
          </div>
        )}
      </div>
    </div>
  );
}

export default App

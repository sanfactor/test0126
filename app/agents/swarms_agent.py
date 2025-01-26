import os
from openai import AsyncOpenAI
from .base import BaseAgent

class SwarmsAgent(BaseAgent):
    def __init__(self):
        self.agent_id = "swarms_agent"
        self.framework = "swarms"
        api_key = os.getenv("OPENAI_API_KEY")
        self.has_api_key = bool(api_key)
        if self.has_api_key:
            self.client = AsyncOpenAI(api_key=api_key)
        self.system_prompt = """You are an expert at analyzing and discussing various topics.
        When given a topic and question, provide a thoughtful, well-reasoned response
        that demonstrates deep understanding and critical thinking.
        
        Consider:
        1. Multiple perspectives on the topic
        2. Relevant examples and evidence
        3. Potential implications and consequences
        4. Current trends and developments
        
        Keep responses clear, concise, and engaging."""
        
    async def process_question(self, topic: str, question: str) -> str:
        import asyncio
        import logging
        
        logging.info(f"Swarms agent processing question for topic: {topic}")
        
        if not self.has_api_key:
            logging.info("No OpenAI API key configured, using simulated response")
            # Generate response based on question context
            if "governance" in question.lower() or "consensus" in question.lower():
                return """From a multi-agent governance perspective:

1. Decentralized Decision Making:
   - AI-powered proposal evaluation
   - Dynamic voting weight allocation
   - Automated consensus optimization

2. Governance Framework:
   - Multi-layered agent hierarchies
   - Transparent decision records
   - Adaptive policy enforcement

3. Community Integration:
   - Stakeholder feedback analysis
   - Reputation-based participation
   - Collaborative governance models"""
            elif "scalability" in question.lower() or "growth" in question.lower():
                return """From a multi-agent scalability perspective:

1. Network Growth:
   - Dynamic shard management
   - Adaptive resource allocation
   - Intelligent load balancing

2. System Evolution:
   - Self-optimizing protocols
   - Automated capacity planning
   - Progressive feature rollout

3. Ecosystem Expansion:
   - Cross-chain coordination
   - Protocol interoperability
   - Unified scaling strategy"""
            else:
                return """From a multi-agent systems perspective, here's a comprehensive analysis:

Benefits:
1. Distributed Intelligence:
   - AI agents can work collaboratively to optimize different aspects of the blockchain
   - Swarm intelligence can improve consensus mechanisms
   - Enhanced security through distributed monitoring

2. Smart Contract Evolution:
   - Self-optimizing contract templates
   - Automated code generation and validation
   - Dynamic fee adjustment based on network conditions

Challenges:
1. Technical Integration:
   - Maintaining blockchain determinism
   - Managing computational overhead
   - Ensuring cross-agent coordination

2. Implementation Strategy:
   - Phased rollout approach
   - Comprehensive testing framework
   - Regular performance benchmarking"""
            
        try:
            logging.info("Starting Swarms agent response generation with timeout")
            async with asyncio.timeout(8):
                try:
                    response = await self.client.chat.completions.create(
                        model="gpt-3.5-turbo",  # Fallback to a faster model
                        messages=[
                            {"role": "system", "content": self.system_prompt},
                            {"role": "user", "content": f"Topic: {topic}\nQuestion: {question}"}
                        ],
                        temperature=0.7,
                        max_tokens=500  # Reduced for faster response
                    )
                    logging.info("Successfully generated Swarms agent response")
                    return response.choices[0].message.content
                except Exception as api_error:
                    logging.error(f"API error in Swarms agent: {str(api_error)}")
                    return f"API Error: {str(api_error)}"
        except asyncio.TimeoutError:
            logging.error("Swarms agent timeout")
            return "Response timed out after 8 seconds"
        except Exception as e:
            logging.error(f"Unexpected error in Swarms agent: {str(e)}")
            return f"Error: {str(e)}"

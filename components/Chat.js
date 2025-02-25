import { useState } from 'react';

const Chat = () => {
    const [input, setInput] = useState('');
    const [messages, setMessages] = useState([]);
    const [loading, setLoading] = useState(false);
    const [context, setContext] = useState([]);

    const searchVectorStore = async (query) => {
        try {
            const response = await fetch('http://localhost:8000/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query, k: 3 }),
            });
            const data = await response.json();
            return data.results;
        } catch (error) {
            console.error('Error searching vector store:', error);
            return [];
        }
    };

    const handleSend = async () => {
        if (!input.trim()) return;
        
        setLoading(true);
        
        // Get relevant entries from vector store
        const searchResults = await searchVectorStore(input);
        
        // Format the results
        const formattedResults = searchResults.map(result => ({
            headword: result.headword,
            definition: result.definition,
            examples: result.examples || [],
            distance: result.distance
        }));
        
        // Add to messages
        setMessages([...messages, { 
            user: input, 
            results: formattedResults
        }]);
        
        setInput('');
        setLoading(false);
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    return (
        <div className="flex flex-col h-screen max-w-4xl mx-auto p-4">
            <div className="flex-1 space-y-4 overflow-y-auto pb-4">
                {messages.map((msg, index) => (
                    <div key={index} className="space-y-4">
                        <div className="flex items-start justify-end">
                            <div className="bg-blue-500 text-white rounded-lg px-4 py-2 max-w-[80%]">
                                {msg.user}
                            </div>
                        </div>
                        <div className="flex items-start">
                            <div className="bg-gray-100 rounded-lg px-4 py-2 max-w-[80%] w-full">
                                {msg.results.map((result, i) => (
                                    <div key={i} className="mb-6 last:mb-0">
                                        <div className="font-bold text-lg mb-2">{result.headword}</div>
                                        <div className="text-gray-700 mb-3">{result.definition}</div>
                                        {result.examples && result.examples.length > 0 && (
                                            <div className="bg-gray-50 rounded p-3">
                                                <div className="font-semibold mb-2">Exemplos:</div>
                                                {result.examples.map((example, j) => (
                                                    <div key={j} className="mb-2 last:mb-0">
                                                        <div className="text-gray-800">{example.original}</div>
                                                        <div className="text-gray-600 text-sm">{example.translation}</div>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                        <div className="text-xs text-gray-400 mt-2">Similaridade: {(1 - result.distance).toFixed(3)}</div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                ))}
                {loading && (
                    <div className="flex items-center justify-center py-4">
                        <div className="animate-pulse text-gray-500">
                            Searching context and generating response, it may take ~30 seconds...
                        </div>
                    </div>
                )}
            </div>
            <div className="border-t pt-4">
                <div className="flex space-x-4">
                    <input
                        className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyPress={handleKeyPress}
                        placeholder="Ask about the Yanomami people..."
                        disabled={loading}
                    />
                    <button
                        className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
                        onClick={handleSend}
                        disabled={loading || !input.trim()}
                    >
                        Send
                    </button>
                </div>
            </div>
        </div>
    );
};

export default Chat;

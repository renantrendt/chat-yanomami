import { useState } from 'react';

const Chat = () => {
    const [input, setInput] = useState('');
    const [messages, setMessages] = useState([]);
    const [loading, setLoading] = useState(false);

    const handleSend = async () => {
        if (!input.trim()) return;
        
        setLoading(true);
        const response = await fetch('/api/inference', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: input }),
        });
        const data = await response.json();
        setMessages([...messages, { user: input, bot: data.output }]);
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
                            <div className="bg-gray-200 rounded-lg px-4 py-2 max-w-[80%]">
                                {msg.bot}
                            </div>
                        </div>
                    </div>
                ))}
                {loading && (
                    <div className="flex items-center justify-center py-4">
                        <div className="animate-pulse text-gray-500">
                            Generating response (this may take up to 30 seconds)...
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
                        placeholder="Type your message..."
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

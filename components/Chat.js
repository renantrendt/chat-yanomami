import { useState } from 'react';

const Chat = () => {
    const [input, setInput] = useState('');
    const [messages, setMessages] = useState([]);
    const [loading, setLoading] = useState(false); // State for loading message

    const handleSend = async () => {
        setLoading(true); // Set loading to true when sending a query
        const response = await fetch('/api/inference', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: input }),
        });
        const data = await response.json();
        setMessages([...messages, { user: input, bot: data.output }]);
        setInput('');
        setLoading(false); // Set loading to false after receiving a response
    };

    return (
        <div>
            <div>
                {messages.map((msg, index) => (
                    <div key={index}>
                        <strong>User:</strong> {msg.user}
                        <br />
                        <strong>Bot:</strong> {msg.bot}
                    </div>
                ))}
            </div>
            {loading && <p>Loading answer...</p>} {/* Show loading message */}
            <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Type your message..."
            />
            <button onClick={handleSend}>Send</button>
        </div>
    );
};

export default Chat;

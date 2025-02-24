import { exec } from 'child_process';

export default function handler(req, res) {
    const { query } = req.body;

    exec(`python /Users/renanserrano/CascadeProjects/mobilellm125m/MobileLLM/inference.py "${query}"`, (error, stdout, stderr) => {
        if (error) {
            console.error(`Error running inference: ${error}`);
            console.error(`stderr: ${stderr}`);
            return res.status(500).json({ message: 'Error running inference', logs: stderr });
        }
        
        console.log(`Inference output: ${stdout}`);
        console.log(`stderr: ${stderr}`);
        
        // Ensure that the response is sent back to the client
        return res.status(200).json({ output: stdout, logs: stderr });
    });
}
const express = require('express');
const app = express();
const PORT = 5000;

// Replace this with your actual collection UID
const COLLECTION_UID = 'YOUR_COLLECTION_UID_HERE'; // e.g., '12345678-abcd-1234-efgh-567890abcdef'

app.get('/docs/collection', async (req, res) => {
    const apiKey = process.env.POSTMAN_API_KEY;
    
    if (!apiKey) {
        return res.status(500).json({ error: 'POSTMAN_API_KEY environment variable is not set' });
    }

    try {
        const response = await fetch(`https://api.getpostman.com/collections/${COLLECTION_UID}`, {
            method: 'GET',
            headers: {
                'X-Api-Key': apiKey
            }
        });

        if (!response.ok) {
            const errorData = await response.json();
            console.error('Postman API Error:', response.status, errorData);
            return res.status(response.status).json({ 
                error: 'Postman API request failed', 
                details: errorData 
            });
        }

        const data = await response.json();
        res.json(data.collection);
    } catch (error) {
        console.error('Server Error:', error.message);
        res.status(500).json({ error: 'Failed to fetch collection', details: error.message });
    }
});

app.listen(PORT, () => {
    console.log(`Server running at http://127.0.0.1:${PORT}`);
    console.log(`Test endpoint: http://127.0.0.1:${PORT}/docs/collection`);
});